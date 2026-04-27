"""Runtime configuration (env vars)."""

from __future__ import annotations

import os
from pathlib import Path


def _repo_root() -> Path:
    # backend/app/config.py -> parents[2] = repo root
    return Path(__file__).resolve().parents[2]


def default_artifacts_dir() -> Path:
    return _repo_root() / "artifacts"


def model_weight_path() -> Path:
    raw = os.getenv("MODEL_WEIGHT_PATH", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return default_artifacts_dir() / "best.pt"


def class_names_path() -> Path:
    raw = os.getenv("CLASS_NAMES_PATH", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return default_artifacts_dir() / "class_names.json"


def confidence_threshold() -> float:
    return float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))


def rejection_confidence_threshold() -> float:
    """
    Below this value, prediction is rejected as likely unsupported crop / out-of-distribution.
    Keep this higher than confidence_threshold to reduce forced mislabels on unseen crops.
    """
    return float(os.getenv("REJECTION_CONFIDENCE_THRESHOLD", "0.65"))


def prediction_margin_threshold() -> float:
    """
    Minimum gap between top-1 and top-2 probabilities required to accept prediction.
    Lower gap means ambiguous / likely out-of-distribution.
    """
    return float(os.getenv("PREDICTION_MARGIN_THRESHOLD", "0.18"))


def min_image_bytes() -> int:
    return int(os.getenv("MIN_IMAGE_BYTES", "800"))


def auto_bootstrap_weights() -> bool:
    """If true and weights are missing, create tiny placeholder weights on startup (not plant-trained)."""
    return os.getenv("AGRI_SCAN_AUTO_BOOTSTRAP", "0").strip().lower() not in ("0", "false", "no", "off")


def training_dataset_dir() -> Path | None:
    """ImageFolder root you used (or will use) with train.py — used for alignment checks and optional mirrored saves."""
    raw = os.getenv("TRAINING_DATASET_DIR", "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def user_uploads_dir() -> Path:
    raw = os.getenv("USER_UPLOADS_DIR", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return _repo_root() / "data" / "user_uploads"


def persist_uploads_enabled() -> bool:
    return os.getenv("AGRI_SCAN_SAVE_UPLOADS", "1").strip().lower() not in ("0", "false", "no", "off")


def copy_into_training_class_folders() -> bool:
    """If true, also copy each accepted scan into TRAINING_DATASET_DIR/<predicted class>/ (use with care)."""
    return os.getenv("AGRI_SCAN_SAVE_TO_TRAINING_FOLDERS", "0").strip().lower() in ("1", "true", "yes", "on")
