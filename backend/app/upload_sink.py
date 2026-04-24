"""Persist scan uploads under data/user_uploads and optionally link to TRAINING_DATASET_DIR."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import (
    copy_into_training_class_folders,
    persist_uploads_enabled,
    training_dataset_dir,
    user_uploads_dir,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]

logger = logging.getLogger(__name__)


def _ext_for_bytes(data: bytes) -> str:
    if len(data) >= 2 and data[:2] == b"\xff\xd8":
        return ".jpg"
    if len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    return ".bin"


def persist_scan_upload(
    image_bytes: bytes,
    *,
    crop: str,
    disease: str | None,
    class_id: int,
    confidence: float,
    rejected: bool,
    rejection_reason: str | None,
    uncertain: bool,
) -> dict[str, Any]:
    """Save file + manifest line; optionally mirror into training ImageFolder. Returns JSON fragment for /predict."""
    if not persist_uploads_enabled():
        return {}

    root = user_uploads_dir()
    ts = datetime.now(timezone.utc)
    day = ts.strftime("%Y-%m-%d")
    uid = uuid.uuid4().hex[:10]
    ext = _ext_for_bytes(image_bytes)
    sub = "rejected" if rejected else "scans"
    out_dir = root / sub / day
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{ts.strftime('%H%M%S')}_{crop}_{uid}{ext}"
    out_path = out_dir / fname
    out_path.write_bytes(image_bytes)

    manifest = root / "manifest.jsonl"
    try:
        rel = str(out_path.resolve().relative_to(_REPO_ROOT))
    except ValueError:
        rel = None
    record = {
        "utc": ts.isoformat(),
        "saved_path": str(out_path.resolve()),
        "relative_to_repo": rel,
        "crop": crop,
        "disease": disease,
        "class_id": class_id,
        "confidence": confidence,
        "uncertain": uncertain,
        "rejected": rejected,
        "rejection_reason": rejection_reason,
    }

    training_root = training_dataset_dir()
    matching_folder: str | None = None
    mirrored_into_dataset: str | None = None

    if training_root and training_root.is_dir() and disease and not rejected:
        candidate = training_root / disease
        if candidate.is_dir():
            matching_folder = disease
        if copy_into_training_class_folders() and matching_folder:
            dest_dir = training_root / matching_folder
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / f"upload_{ts.strftime('%Y%m%d_%H%M%S')}_{uid}{ext}"
            dest_file.write_bytes(image_bytes)
            mirrored_into_dataset = str(dest_file.resolve())
            logger.info("Mirrored upload into training folder: %s", dest_file)

    record["training_dataset_dir"] = str(training_root) if training_root else None
    record["matching_training_folder"] = matching_folder
    record["mirrored_into_dataset_path"] = mirrored_into_dataset

    with open(manifest, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {
        "storage": {
            "saved_file": str(out_path.resolve()),
            "manifest": str(manifest.resolve()),
            "training_dataset_configured": training_root is not None and training_root.is_dir(),
            "matching_training_folder": matching_folder,
            "mirrored_into_dataset": mirrored_into_dataset,
        }
    }
