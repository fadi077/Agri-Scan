"""Loads a classifier checkpoint: ResNet18 (real training) or tiny CNN (bootstrap placeholder)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from PIL import Image, UnidentifiedImageError
from torchvision import models, transforms

from app.tiny_cnn import SmallCNN

logger = logging.getLogger(__name__)


IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def _device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _crop_allowed_indices(class_names: list[str], crop: str) -> list[int]:
    if crop == "any":
        return list(range(len(class_names)))
    key = crop.lower().strip()
    aliases = {"tomato": "tomato", "potato": "potato", "pepper": "pepper"}
    needle = aliases.get(key, key)
    idx = [i for i, name in enumerate(class_names) if needle in name.lower()]
    return idx


@dataclass
class PredictionResult:
    disease: str
    confidence: float
    class_id: int
    uncertain: bool
    top_predictions: list[dict[str, Any]]


def _is_resnet_state_dict(state: dict[str, Any]) -> bool:
    return any(k.startswith("conv1.") or k.startswith("layer1.") for k in state)


class ClassifierRuntime:
    def __init__(
        self,
        *,
        weights_path: Path,
        class_names_path: Path,
        confidence_threshold: float,
        min_image_bytes: int,
    ) -> None:
        self.weights_path = weights_path
        self.class_names_path = class_names_path
        self.confidence_threshold: float = confidence_threshold
        self.min_image_bytes = min_image_bytes

        self._device = _device()
        with open(class_names_path, encoding="utf-8") as f:
            self.class_names: list[str] = json.load(f)
        if not self.class_names:
            raise ValueError("class_names.json is empty")

        num_classes = len(self.class_names)
        raw: Any = torch.load(weights_path, map_location=self._device, weights_only=False)

        if isinstance(raw, dict) and raw.get("version") == 2 and raw.get("arch") == "tiny_cnn":
            self.arch = "tiny_cnn"
            self.diagnostic_ready = bool(raw.get("diagnostic_ready", False))
            input_size = int(raw.get("input_size", 64))
            net = SmallCNN(num_classes)
            net.load_state_dict(raw["state_dict"])
            net.to(self._device)
            net.eval()
            self._model = net
            self._tfm = transforms.Compose(
                [
                    transforms.Resize(input_size),
                    transforms.CenterCrop(input_size),
                    transforms.ToTensor(),
                    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
                ]
            )
        else:
            self.arch = "resnet18"
            self.diagnostic_ready = True
            if isinstance(raw, dict) and "state_dict" in raw and "version" not in raw:
                state = raw["state_dict"]
            else:
                state = raw
            if not isinstance(state, dict) or not _is_resnet_state_dict(state):
                raise ValueError("Checkpoint is not ResNet18 state_dict or v2 tiny_cnn bundle")
            net = models.resnet18(weights=None)
            net.fc = nn.Linear(net.fc.in_features, num_classes)
            net.load_state_dict(state)
            net.to(self._device)
            net.eval()
            self._model = net
            self._tfm = transforms.Compose(
                [
                    transforms.Resize(256),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
                ]
            )

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

        x = self._tfm(img).unsqueeze(0).to(self._device)
        with torch.inference_mode():
            logits = self._model(x)[0]
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


def try_load_classifier(
    weights_path: Path,
    class_names_path: Path,
    confidence_threshold: float,
    min_image_bytes: int,
) -> ClassifierRuntime | None:
    if not weights_path.is_file():
        logger.warning("Model weights not found at %s", weights_path)
        return None
    if not class_names_path.is_file():
        logger.warning("Class names file not found at %s", class_names_path)
        return None
    try:
        return ClassifierRuntime(
            weights_path=weights_path,
            class_names_path=class_names_path,
            confidence_threshold=confidence_threshold,
            min_image_bytes=min_image_bytes,
        )
    except Exception:
        logger.exception("Failed to load classifier from %s", weights_path)
        return None
