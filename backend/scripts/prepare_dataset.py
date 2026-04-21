from __future__ import annotations

import random
import shutil
from pathlib import Path


def find_source_root(dataset_root: Path) -> Path:
    candidates = []
    for directory in dataset_root.rglob("*"):
        if not directory.is_dir():
            continue
        child_dirs = [p for p in directory.iterdir() if p.is_dir()]
        if not child_dirs:
            continue
        image_count = 0
        for child in child_dirs:
            image_count += len(list(child.glob("*.jpg"))) + len(list(child.glob("*.JPG"))) + len(
                list(child.glob("*.png"))
            )
        if image_count > 0:
            candidates.append((image_count, directory))

    if not candidates:
        raise FileNotFoundError(
            f"No class-directory image dataset found under {dataset_root}."
        )

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def split_class_dir(
    class_dir: Path,
    output_root: Path,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
) -> None:
    files = [p for p in class_dir.glob("*") if p.is_file()]
    random.shuffle(files)

    train_end = int(len(files) * train_ratio)
    val_end = train_end + int(len(files) * val_ratio)

    subsets = {
        "train": files[:train_end],
        "val": files[train_end:val_end],
        "test": files[val_end:],
    }

    for split_name, split_files in subsets.items():
        target_dir = output_root / split_name / class_dir.name
        target_dir.mkdir(parents=True, exist_ok=True)
        for src in split_files:
            shutil.copy2(src, target_dir / src.name)


def main() -> None:
    random.seed(42)
    dataset_root = (
        Path.home()
        / ".cache"
        / "kagglehub"
        / "datasets"
        / "emmarex"
        / "plantdisease"
        / "versions"
        / "1"
    )
    output_root = Path.cwd() / "data" / "processed"

    if not dataset_root.exists():
        raise FileNotFoundError(f"Dataset root not found at {dataset_root}. Run download script.")

    source_root = find_source_root(dataset_root)

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    class_dirs = [p for p in source_root.iterdir() if p.is_dir()]
    if not class_dirs:
        raise RuntimeError("No class folders found in source dataset.")

    for class_dir in class_dirs:
        split_class_dir(class_dir, output_root)

    print(f"Source dataset root: {source_root}")
    print(f"Prepared dataset at: {output_root}")


if __name__ == "__main__":
    main()
