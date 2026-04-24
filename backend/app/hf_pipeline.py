"""Hugging Face image-classification backend (PlantVillage-style labels, zero manual training)."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from typing import Any

import torch
from PIL import Image, UnidentifiedImageError

from app.config import default_artifacts_dir
from app.model import PredictionResult, _crop_allowed_indices

logger = logging.getLogger(__name__)

DEFAULT_HF_MODEL = "mesabo/agri-plant-disease-resnet50"


class HfPlantClassifier:
    """Transformers ResNetForImageClassification — real pretrained weights, ~95MB first download."""

    def __init__(
        self,
        *,
        model_id: str,
        local_dir: Path,
        confidence_threshold: float,
        min_image_bytes: int,
    ) -> None:
        from transformers import AutoImageProcessor, AutoModelForImageClassification

        self.model_id = model_id
        self.source = f"huggingface:{model_id}"
        self.arch = "hf-resnet50"
        self.diagnostic_ready = True
        self.confidence_threshold = confidence_threshold
        self.min_image_bytes = min_image_bytes
        self.weights_path = str(local_dir)

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        local_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "Loading Hugging Face model %s (first run may download ~95MB — one-time)...",
            model_id,
        )
        self._processor = AutoImageProcessor.from_pretrained(model_id, cache_dir=str(local_dir))
        self._model = AutoModelForImageClassification.from_pretrained(model_id, cache_dir=str(local_dir))
        self._model.to(self._device)
        self._model.eval()

        id2label = self._model.config.id2label
        n = len(id2label)
        self.class_names: list[str] = [id2label[str(i)] for i in range(n)]

    @property
    def class_count(self) -> int:
        return len(self.class_names)

    def predict(self, image_bytes: bytes, crop: str) -> PredictionResult:
        if len(image_bytes) < self.min_image_bytes:
            raise ValueError("IMAGE_TOO_SMALL")

        try:
            img = Image.open(BytesIO(image_bytes)).convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as e:
            raise ValueError("INVALID_IMAGE") from e

        w, h = img.size
        if w < 64 or h < 64:
            raise ValueError("IMAGE_TOO_SMALL_DIM")

        allowed = _crop_allowed_indices(self.class_names, crop)
        if not allowed:
            raise ValueError("NO_CLASSES_FOR_CROP")

        inputs = self._processor(images=img, return_tensors="pt")
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.inference_mode():
            logits = self._model(**inputs).logits[0]

        if crop != "any":
            mask = torch.full_like(logits, float("-inf"))
            for i in allowed:
                mask[i] = logits[i]
            logits = mask

        probs = torch.softmax(logits, dim=0)
        top_p, top_i = torch.topk(probs, k=min(3, probs.numel()))

        pairs = [(int(top_i[j]), float(top_p[j])) for j in range(top_i.numel())]
        best_id, best_conf = pairs[0]
        disease = self.class_names[best_id]
        uncertain = best_conf < self.confidence_threshold

        top_predictions = [
            {"disease": self.class_names[i], "confidence": round(c, 4), "class_id": i} for i, c in pairs
        ]

        return PredictionResult(
            disease=disease,
            confidence=round(best_conf, 4),
            class_id=best_id,
            uncertain=uncertain,
            top_predictions=top_predictions,
        )


def hf_cache_root() -> Path:
    return default_artifacts_dir() / "hf_hub_cache"


def hf_model_id() -> str | None:
    import os

    raw = os.getenv("AGRI_SCAN_HF_MODEL", DEFAULT_HF_MODEL).strip()
    if raw.lower() in ("", "none", "off", "false", "0", "disable"):
        return None
    return raw


def try_load_hf_classifier(
    confidence_threshold: float,
    min_image_bytes: int,
) -> HfPlantClassifier | None:
    mid = hf_model_id()
    if not mid:
        return None
    try:
        return HfPlantClassifier(
            model_id=mid,
            local_dir=hf_cache_root(),
            confidence_threshold=confidence_threshold,
            min_image_bytes=min_image_bytes,
        )
    except Exception:
        logger.exception("Failed to load Hugging Face baseline model %s", mid)
        return None
