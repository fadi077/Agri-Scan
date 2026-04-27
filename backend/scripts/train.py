"""
Train and evaluate a ResNet18 leaf-disease classifier from ImageFolder data.

Expected layouts:
1) Explicit split directories:
   data/processed/
     train/<class_name>/*.jpg
     val/<class_name>/*.jpg
     test/<class_name>/*.jpg
2) Single directory fallback:
   data_dir/<class_name>/*.jpg
   (script creates a stratified train/val split)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, Subset, WeightedRandomSampler
from torchvision import datasets, models, transforms

IMG_EXTS = {".jpg", ".jpeg", ".png", ".ppm", ".bmp", ".pgm", ".tif", ".tiff", ".webp"}
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


def _class_has_images(class_dir: Path) -> bool:
    for p in class_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMG_EXTS:
            return True
    return False


class LenientImageFolder(datasets.ImageFolder):
    """ImageFolder variant that skips empty class directories."""

    def find_classes(self, directory: str):
        root = Path(directory)
        classes = []
        skipped = []
        for p in sorted([d for d in root.iterdir() if d.is_dir()]):
            if _class_has_images(p):
                classes.append(p.name)
            else:
                skipped.append(p.name)

        if skipped:
            print(f"Skipping empty/non-image class folders: {', '.join(skipped)}")
        if not classes:
            raise FileNotFoundError(f"No valid class folders with images found under {directory}")
        class_to_idx = {name: i for i, name in enumerate(classes)}
        return classes, class_to_idx


def _subsample_imagefolder(
    full_ds: LenientImageFolder, train_subset: Subset, max_samples: int, seed: int
) -> Subset:
    """
    Randomly downsample a training subset to cap wall-clock for quick A/B tests.
    Keeps a stratified mix by walking class indices in the base dataset.
    """
    g = torch.Generator().manual_seed(seed)
    targets = [int(train_subset.dataset.samples[i][1]) for i in train_subset.indices]
    if len(targets) <= max_samples:
        return train_subset

    by_class: dict[int, list[int]] = defaultdict(list)
    for rel_pos, t in enumerate(targets):
        by_class[t].append(rel_pos)
    k = min(max_samples, len(targets))
    per = max(1, k // max(1, len(full_ds.classes)))
    rel_keep: set[int] = set()
    for cls, rel_indices in by_class.items():
        take = min(per, len(rel_indices))
        perm = torch.randperm(len(rel_indices), generator=g).tolist()[:take]
        for i in perm:
            rel_keep.add(rel_indices[i])

    rel_list = list(rel_keep)
    if len(rel_list) < k:
        remaining = [i for i in range(len(targets)) if i not in rel_keep]
        perm = torch.randperm(len(remaining), generator=g).tolist()
        for idx in perm:
            if len(rel_list) >= k:
                break
            rel_list.append(remaining[idx])

    new_indices = [train_subset.indices[i] for i in sorted(set(rel_list))]
    print(f"Subsampled training set: {len(train_subset)} -> {len(new_indices)} (cap={max_samples})")
    return Subset(train_subset.dataset, new_indices)


def _random_subset(dataset: torch.utils.data.Dataset, max_items: int, seed: int) -> Subset:
    if max_items <= 0 or len(dataset) <= max_items:
        return Subset(dataset, list(range(len(dataset))))
    g = torch.Generator().manual_seed(seed)
    picked = torch.randperm(len(dataset), generator=g)[:max_items].tolist()
    print(f"Subsampled eval set: {len(dataset)} -> {len(picked)} (cap={max_items})")
    return Subset(dataset, picked)


def build_train_transform(enable_augmentations: bool) -> transforms.Compose:
    if not enable_augmentations:
        return transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(MEAN, STD),
            ]
        )
    return transforms.Compose(
        [
            transforms.RandomResizedCrop(224, scale=(0.75, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=12),
            transforms.ColorJitter(brightness=0.18, contrast=0.18, saturation=0.12, hue=0.03),
            transforms.ToTensor(),
            transforms.Normalize(MEAN, STD),
        ]
    )


def build_eval_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(MEAN, STD),
        ]
    )


def stratified_split_indices(targets: list[int], val_fraction: float, seed: int) -> tuple[list[int], list[int]]:
    by_class: dict[int, list[int]] = defaultdict(list)
    for idx, target in enumerate(targets):
        by_class[target].append(idx)

    g = torch.Generator().manual_seed(seed)
    train_idx: list[int] = []
    val_idx: list[int] = []

    for cls, indices in by_class.items():
        perm = torch.randperm(len(indices), generator=g).tolist()
        shuffled = [indices[i] for i in perm]
        n_val = max(1, int(math.floor(len(shuffled) * val_fraction)))
        n_val = min(len(shuffled) - 1, n_val) if len(shuffled) > 1 else 1
        cls_val = shuffled[:n_val]
        cls_train = shuffled[n_val:] if len(shuffled) > 1 else []
        if not cls_train:
            cls_train = cls_val[:]
            cls_val = []
        train_idx.extend(cls_train)
        val_idx.extend(cls_val)
        print(f"Class {cls}: train={len(cls_train)} val={len(cls_val)}")

    return train_idx, val_idx


def evaluate_model(
    net: nn.Module,
    loader: DataLoader,
    num_classes: int,
    device: torch.device,
    criterion: nn.Module,
    tag: str = "eval",
) -> dict[str, object]:
    net.eval()
    total = 0
    correct = 0
    loss_total = 0.0
    cm = torch.zeros((num_classes, num_classes), dtype=torch.int64)
    num_batches = max(1, len(loader))

    with torch.inference_mode():
        for batch_i, (x, y) in enumerate(loader, start=1):
            if batch_i == 1 or batch_i == num_batches or batch_i % 25 == 0:
                print(f"  {tag} batch {batch_i}/{num_batches}", flush=True)
            x, y = x.to(device), y.to(device)
            logits = net(x)
            loss = criterion(logits, y)
            pred = logits.argmax(dim=1)
            total += y.size(0)
            correct += int((pred == y).sum())
            loss_total += loss.item() * y.size(0)
            for t, p in zip(y.detach().cpu(), pred.detach().cpu()):
                cm[int(t), int(p)] += 1

    precision = []
    recall = []
    f1 = []
    for i in range(num_classes):
        tp = cm[i, i].item()
        fp = int(cm[:, i].sum().item()) - tp
        fn = int(cm[i, :].sum().item()) - tp
        p = tp / max(1, tp + fp)
        r = tp / max(1, tp + fn)
        f = 0.0 if (p + r) == 0 else 2 * p * r / (p + r)
        precision.append(p)
        recall.append(r)
        f1.append(f)

    return {
        "loss": loss_total / max(1, total),
        "accuracy": correct / max(1, total),
        "macro_precision": sum(precision) / max(1, num_classes),
        "macro_recall": sum(recall) / max(1, num_classes),
        "macro_f1": sum(f1) / max(1, num_classes),
        "per_class_precision": precision,
        "per_class_recall": recall,
        "per_class_f1": f1,
        "confusion_matrix": cm.tolist(),
        "total_samples": total,
    }


def _load_backbone(pretrained: bool) -> nn.Module:
    if pretrained:
        try:
            weights = models.ResNet18_Weights.IMAGENET1K_V1
            print("Using ImageNet pretrained ResNet18 weights.")
            return models.resnet18(weights=weights)
        except Exception as exc:  # noqa: BLE001
            print(f"Warning: failed to load pretrained weights ({exc}). Falling back to random init.")
    print("Using randomly initialized ResNet18 weights.")
    return models.resnet18(weights=None)


def _sampler_for_subset(train_subset: Subset, sampler_mode: str) -> WeightedRandomSampler | None:
    targets = [int(train_subset.dataset.samples[i][1]) for i in train_subset.indices]
    counts = Counter(targets)
    max_count = max(counts.values())
    min_count = min(counts.values())
    imbalance_ratio = max_count / max(1, min_count)
    print(f"Class imbalance ratio (max/min): {imbalance_ratio:.2f}")

    use_weighted = sampler_mode == "weighted" or (sampler_mode == "auto" and imbalance_ratio > 1.25)
    if not use_weighted:
        return None

    sample_weights = [1.0 / counts[t] for t in targets]
    sampler = WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.double),
        num_samples=len(sample_weights),
        replacement=True,
    )
    print("Using weighted random sampler for class balancing.")
    return sampler


def _format_metric(name: str, metrics: dict[str, object]) -> str:
    return (
        f"{name}: loss={metrics['loss']:.4f} acc={metrics['accuracy']:.4f} "
        f"macro_f1={metrics['macro_f1']:.4f} macro_precision={metrics['macro_precision']:.4f} "
        f"macro_recall={metrics['macro_recall']:.4f}"
    )


def main() -> int:
    # Background jobs / redirected stdout are often block-buffered; make logs visible in CI and terminals.
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except Exception:
        pass

    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=Path, required=True, help="ImageFolder train dir, or parent containing train/val/test")
    p.add_argument("--out-dir", type=Path, default=Path("../artifacts"), help="Where to save best.pt and class_names.json")
    p.add_argument("--epochs", type=int, default=12)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--val-fraction", type=float, default=0.15, help="Used only when val split directory is absent")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--workers", type=int, default=0)
    p.add_argument("--sampler", choices=("auto", "weighted", "none"), default="auto")
    p.add_argument("--no-pretrained", action="store_true", help="Disable ImageNet initialization")
    p.add_argument("--no-augment", action="store_true", help="Disable train-time data augmentation")
    p.add_argument(
        "--subsample-train",
        type=int,
        default=0,
        help="Optional cap on training samples for quick A/B tests (0 disables)",
    )
    p.add_argument(
        "--subsample-val",
        type=int,
        default=0,
        help="Optional cap on validation samples (0 = use full val split)",
    )
    p.add_argument(
        "--subsample-test",
        type=int,
        default=0,
        help="Optional cap on test samples (0 = use full test split)",
    )
    args = p.parse_args()

    data_dir = args.data_dir.expanduser().resolve()
    if not data_dir.is_dir():
        print(f"Error: data dir not found: {data_dir}", file=sys.stderr)
        return 1

    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    train_tfm = build_train_transform(enable_augmentations=not args.no_augment)
    eval_tfm = build_eval_transform()

    # Supports either explicit split roots or a single directory that needs splitting.
    if (data_dir / "train").is_dir():
        train_root = data_dir / "train"
        val_root = data_dir / "val"
        test_root = data_dir / "test"
    else:
        train_root = data_dir
        val_root = None
        test_root = None

    train_ds = LenientImageFolder(str(train_root), transform=train_tfm)
    if len(train_ds.classes) < 2:
        print("Error: need at least 2 classes (subfolders) in training data.", file=sys.stderr)
        return 1

    classes = train_ds.classes
    num_classes = len(classes)
    print(f"Loaded {len(train_ds)} training images across {num_classes} classes.")

    if val_root and val_root.is_dir():
        val_ds = LenientImageFolder(str(val_root), transform=eval_tfm)
        if val_ds.classes != classes:
            print("Error: val classes do not match train classes.", file=sys.stderr)
            return 1
        train_loader_ds = train_ds
        print(f"Loaded explicit val split: {len(val_ds)} images.")
    else:
        full_eval_ds = LenientImageFolder(str(train_root), transform=eval_tfm)
        train_idx, val_idx = stratified_split_indices(full_eval_ds.targets, args.val_fraction, args.seed)
        if not val_idx:
            print("Error: val split is empty; increase dataset size or val-fraction.", file=sys.stderr)
            return 1
        train_loader_ds = Subset(train_ds, train_idx)
        val_ds = Subset(full_eval_ds, val_idx)
        print(f"Using stratified split from train: train={len(train_idx)} val={len(val_idx)}")

    if test_root and test_root.is_dir():
        test_ds = LenientImageFolder(str(test_root), transform=eval_tfm)
        if test_ds.classes != classes:
            print("Error: test classes do not match train classes.", file=sys.stderr)
            return 1
        print(f"Loaded explicit test split: {len(test_ds)} images.")
    else:
        test_ds = None
        print("No explicit test split found; test metrics will be skipped.")

    if args.subsample_train and args.subsample_train > 0:
        if isinstance(train_loader_ds, Subset):
            train_loader_ds = _subsample_imagefolder(
                full_ds=train_ds, train_subset=train_loader_ds, max_samples=int(args.subsample_train), seed=args.seed
            )
        else:
            full_subset = Subset(train_ds, list(range(len(train_ds))))
            train_loader_ds = _subsample_imagefolder(
                full_ds=train_ds, train_subset=full_subset, max_samples=int(args.subsample_train), seed=args.seed
            )

    if args.subsample_val and args.subsample_val > 0:
        val_ds = _random_subset(val_ds, int(args.subsample_val), args.seed + 1)
    if test_ds and args.subsample_test and args.subsample_test > 0:
        test_ds = _random_subset(test_ds, int(args.subsample_test), args.seed + 2)

    sampler = _sampler_for_subset(train_loader_ds, args.sampler) if isinstance(train_loader_ds, Subset) else None
    if sampler is None and args.sampler == "weighted" and not isinstance(train_loader_ds, Subset):
        subset = Subset(train_ds, list(range(len(train_ds))))
        sampler = _sampler_for_subset(subset, args.sampler)

    train_loader = DataLoader(
        train_loader_ds,
        batch_size=args.batch_size,
        shuffle=sampler is None,
        sampler=sampler,
        num_workers=args.workers,
    )
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.workers) if test_ds else None

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    net = _load_backbone(pretrained=not args.no_pretrained)
    net.fc = nn.Linear(net.fc.in_features, num_classes)
    net.to(device)

    opt = torch.optim.AdamW(net.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(2, args.epochs))
    criterion = nn.CrossEntropyLoss()

    best_val = 0.0
    best_epoch = -1
    best_state: dict[str, torch.Tensor] | None = None
    history: list[dict[str, float]] = []

    for epoch in range(args.epochs):
        net.train()
        train_loss_total = 0.0
        train_correct = 0
        train_total = 0
        train_steps = max(1, len(train_loader))

        for batch_i, (x, y) in enumerate(train_loader, start=1):
            if batch_i == 1 or batch_i == train_steps or batch_i % 10 == 0:
                print(f"  train batch {batch_i}/{train_steps} (epoch {epoch + 1}/{args.epochs})", flush=True)
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            logits = net(x)
            loss = criterion(logits, y)
            loss.backward()
            opt.step()

            train_loss_total += loss.item() * x.size(0)
            train_correct += int((logits.argmax(dim=1) == y).sum())
            train_total += x.size(0)

        scheduler.step()
        train_loss = train_loss_total / max(1, train_total)
        train_acc = train_correct / max(1, train_total)
        val_metrics = evaluate_model(net, val_loader, num_classes, device, criterion, tag="val")
        val_acc = float(val_metrics["accuracy"])

        history.append(
            {
                "epoch": float(epoch + 1),
                "train_loss": train_loss,
                "train_acc": train_acc,
                "val_loss": float(val_metrics["loss"]),
                "val_acc": val_acc,
                "val_macro_f1": float(val_metrics["macro_f1"]),
                "lr": opt.param_groups[0]["lr"],
            }
        )
        print(
            f"epoch {epoch + 1}/{args.epochs} "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_metrics['loss']:.4f} val_acc={val_acc:.4f} val_macro_f1={val_metrics['macro_f1']:.4f}"
        )

        if val_acc >= best_val:
            best_val = val_acc
            best_epoch = epoch + 1
            best_state = {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}

    if best_state is None:
        print("Error: no weights captured.", file=sys.stderr)
        return 1

    net.load_state_dict(best_state)
    final_val = evaluate_model(net, val_loader, num_classes, device, criterion, tag="val")
    final_test = (
        evaluate_model(net, test_loader, num_classes, device, criterion, tag="test") if test_loader else None
    )

    weights_path = out_dir / "best.pt"
    names_path = out_dir / "class_names.json"
    metrics_path = out_dir / "metrics.json"
    torch.save(best_state, weights_path)
    with open(names_path, "w", encoding="utf-8") as f:
        json.dump(classes, f, indent=2)

    metrics_body: dict[str, object] = {
        "best_epoch": best_epoch,
        "history": history,
        "val_metrics": final_val,
        "test_metrics": final_test,
        "class_names": classes,
        "config": {
            "data_dir": str(data_dir),
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "lr": args.lr,
            "sampler": args.sampler,
            "pretrained": not args.no_pretrained,
            "augmentations": not args.no_augment,
            "seed": args.seed,
        },
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_body, f, indent=2)

    print(f"Best checkpoint epoch: {best_epoch}")
    print(_format_metric("Validation", final_val))
    if final_test:
        print(_format_metric("Test", final_test))
    print(f"Saved weights to {weights_path}")
    print(f"Saved class list ({len(classes)} classes) to {names_path}")
    print(f"Saved detailed metrics to {metrics_path}")
    print("Set MODEL_WEIGHT_PATH / CLASS_NAMES_PATH if you store them outside the default ../artifacts layout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
