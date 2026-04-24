"""
Train a ResNet18 leaf-disease classifier from an ImageFolder dataset.

Expected layout (ImageFolder):
  data_dir/
    Tomato___Early_blight/
      *.jpg
    Potato___Late_blight/
      ...

Run from the `backend` directory:
  python scripts/train.py --data-dir path/to/dataset --out-dir ../artifacts
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, models, transforms

IMG_EXTS = {".jpg", ".jpeg", ".png", ".ppm", ".bmp", ".pgm", ".tif", ".tiff", ".webp"}


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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=Path, required=True, help="ImageFolder root with one subfolder per class")
    p.add_argument("--out-dir", type=Path, default=Path("../artifacts"), help="Where to save best.pt and class_names.json")
    p.add_argument("--epochs", type=int, default=8)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--val-fraction", type=float, default=0.15)
    args = p.parse_args()

    data_dir = args.data_dir.expanduser().resolve()
    if not data_dir.is_dir():
        print(f"Error: data dir not found: {data_dir}", file=sys.stderr)
        return 1

    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    tfm = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ]
    )

    full = LenientImageFolder(str(data_dir), transform=tfm)
    if len(full.classes) < 2:
        print("Error: need at least 2 classes (subfolders) under data-dir.", file=sys.stderr)
        return 1

    n_val = max(1, int(len(full) * args.val_fraction))
    n_train = len(full) - n_val
    if n_train < 1:
        print("Error: not enough images for train/val split.", file=sys.stderr)
        return 1

    train_ds, val_ds = random_split(
        full,
        [n_train, n_val],
        generator=torch.Generator().manual_seed(42),
    )

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    num_classes = len(full.classes)
    # Avoid network dependency during training setup (works offline).
    net = models.resnet18(weights=None)
    net.fc = nn.Linear(net.fc.in_features, num_classes)
    net.to(device)

    opt = torch.optim.Adam(net.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()

    best_val = 0.0
    best_state: dict[str, torch.Tensor] | None = None

    for epoch in range(args.epochs):
        net.train()
        train_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            logits = net(x)
            loss = criterion(logits, y)
            loss.backward()
            opt.step()
            train_loss += loss.item() * x.size(0)

        net.eval()
        correct = 0
        total = 0
        with torch.inference_mode():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                pred = net(x).argmax(dim=1)
                correct += int((pred == y).sum())
                total += x.size(0)

        acc = correct / max(1, total)
        print(f"epoch {epoch + 1}/{args.epochs}  train_loss={train_loss / max(1, n_train):.4f}  val_acc={acc:.4f}")
        if acc >= best_val:
            best_val = acc
            best_state = {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}

    if best_state is None:
        print("Error: no weights captured.", file=sys.stderr)
        return 1

    weights_path = out_dir / "best.pt"
    names_path = out_dir / "class_names.json"
    torch.save(best_state, weights_path)
    with open(names_path, "w", encoding="utf-8") as f:
        json.dump(full.classes, f, indent=2)

    print(f"Saved weights to {weights_path}")
    print(f"Saved class list ({len(full.classes)} classes) to {names_path}")
    print("Set MODEL_WEIGHT_PATH / CLASS_NAMES_PATH if you store them outside the default ../artifacts layout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
