from __future__ import annotations

import io
import os
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image


@dataclass
class Prediction:
    disease: str
    confidence: float
    class_id: int
    uncertain: bool = False
    top_predictions: List[dict] | None = None
    rejected: bool = False
    rejection_reason: str | None = None


class ModelService:
    """
    Thin prediction service wrapper.
    Replace `_predict_stub` with real TensorFlow model inference when model artifacts are ready.
    """

    def __init__(self) -> None:
        self.model_path = os.getenv("MODEL_PATH", "")
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
        self.uncertain_label = os.getenv("UNCERTAIN_LABEL", "Uncertain - Monitor Closely")
        self.crop_mismatch_threshold = float(os.getenv("CROP_MISMATCH_THRESHOLD", "0.55"))
        self.supported_crops = ["any", "tomato", "potato", "pepper"]
        self.class_names = self._load_class_names()
    def _class_matches_crop(self, class_name: str, selected_crop: str) -> bool:
        value = class_name.lower()
        if selected_crop == "any":
            return True
        if selected_crop == "tomato":
            return "tomato" in value
        if selected_crop == "potato":
            return "potato" in value
        if selected_crop == "pepper":
            return "pepper" in value
        return True

    def _apply_crop_filter(self, top_predictions: List[dict], selected_crop: str) -> List[dict]:
        if selected_crop == "any":
            return top_predictions
        filtered = [
            item
            for item in top_predictions
            if self._class_matches_crop(str(item["disease"]), selected_crop)
        ]
        return filtered

        self._model_loaded = False
        self._model = None

    def _load_class_names(self) -> List[str]:
        class_names_file = os.getenv("CLASS_NAMES_FILE", "artifacts/class_names.txt")
        class_names_path = Path(class_names_file)
        if class_names_path.exists():
            return [line.strip() for line in class_names_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        # Initial MVP classes aligned with the frontend recommendation map.
        return [
            "Healthy",
            "Tomato Early Blight",
            "Tomato Late Blight",
            "Tomato Leaf Curl",
            "Tomato Bacterial Spot",
        ]

    def load(self) -> None:
        """
        Load trained model from MODEL_PATH if available.
        Falls back to deterministic prediction in development.
        """
        if not self.model_path:
            self._model_loaded = False
            return

        try:
            import tensorflow as tf  # Imported lazily to keep startup lightweight without model files

            self._model = tf.keras.models.load_model(self.model_path)
            self._model_loaded = True
        except Exception:
            self._model = None
            self._model_loaded = False

    def _preprocess(self, raw_bytes: bytes) -> Image.Image:
        image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        return image.resize((224, 224))

    def _quality_gate(self, image: Image.Image) -> str | None:
        array = np.array(image, dtype=np.float32)

        brightness = float(array.mean())
        if brightness < 35:
            return "Image is too dark. Retake in natural light."
        if brightness > 235:
            return "Image is overexposed. Avoid direct glare and retake."

        gray = np.dot(array[..., :3], [0.299, 0.587, 0.114])
        blur_score = float(np.var(gray))
        if blur_score < 120:
            return "Image is blurry. Hold camera steady and refocus on one leaf."

        red = array[..., 0]
        green = array[..., 1]
        blue = array[..., 2]
        leaf_like_mask = (green > red + 12) & (green > blue + 12) & (green > 60)
        leaf_ratio = float(leaf_like_mask.mean())
        if leaf_ratio < 0.08:
            return "No clear leaf detected. Fill frame with a single leaf."

        return None

    def _predict_with_model(self, image: Image.Image) -> Tuple[int, float, List[dict]]:
        if self._model is None:
            raise RuntimeError("Model not loaded")

        array = np.array(image, dtype=np.float32)
        array = np.expand_dims(array, axis=0)
        predictions = self._model.predict(array, verbose=0)[0]
        class_id = int(np.argmax(predictions))
        confidence = float(predictions[class_id])
        ranked_indices = np.argsort(predictions)[::-1][:3]
        top_predictions = [
            {
                "disease": self.class_names[int(idx)],
                "confidence": round(float(predictions[int(idx)]), 4),
                "class_id": int(idx),
            }
            for idx in ranked_indices
        ]
        return class_id, round(confidence, 4), top_predictions

    def _predict_stub(self, image: Image.Image) -> Tuple[int, float, List[dict]]:
        # Deterministic fallback to keep demos reproducible before real model integration.
        digest = hashlib.sha256(image.tobytes()).hexdigest()
        class_id = int(digest[:2], 16) % len(self.class_names)
        confidence_seed = int(digest[2:4], 16) / 255
        confidence = round(0.7 + confidence_seed * 0.28, 2)
        second_idx = (class_id + 1) % len(self.class_names)
        third_idx = (class_id + 2) % len(self.class_names)
        second_confidence = round(max(confidence - 0.12, 0.05), 4)
        third_confidence = round(max(confidence - 0.19, 0.03), 4)
        top_predictions = [
            {
                "disease": self.class_names[class_id],
                "confidence": confidence,
                "class_id": class_id,
            },
            {
                "disease": self.class_names[second_idx],
                "confidence": second_confidence,
                "class_id": second_idx,
            },
            {
                "disease": self.class_names[third_idx],
                "confidence": third_confidence,
                "class_id": third_idx,
            },
        ]
        return class_id, confidence, top_predictions

    def predict(self, raw_bytes: bytes, selected_crop: str = "any") -> Prediction:
        selected_crop = selected_crop.lower().strip()
        if selected_crop not in self.supported_crops:
            selected_crop = "any"

        image = self._preprocess(raw_bytes)
        rejection_reason = self._quality_gate(image)
        if rejection_reason:
            return Prediction(
                disease="Invalid Scan - Retake Photo",
                confidence=0.0,
                class_id=-1,
                uncertain=True,
                top_predictions=[],
                rejected=True,
                rejection_reason=rejection_reason,
            )

        if self._model_loaded:
            class_id, confidence, top_predictions = self._predict_with_model(image)
        else:
            class_id, confidence, top_predictions = self._predict_stub(image)

        filtered_top_predictions = self._apply_crop_filter(top_predictions, selected_crop)
        if selected_crop != "any":
            if not filtered_top_predictions:
                return Prediction(
                    disease="Invalid Scan - Retake Photo",
                    confidence=0.0,
                    class_id=-1,
                    uncertain=True,
                    top_predictions=[],
                    rejected=True,
                    rejection_reason=f"Selected crop '{selected_crop}' does not match detected leaf pattern.",
                )
            best_for_crop = filtered_top_predictions[0]
            confidence = float(best_for_crop["confidence"])
            class_id = int(best_for_crop["class_id"])

        disease = self.class_names[class_id]
        uncertain = confidence < self.confidence_threshold
        if selected_crop != "any" and confidence < self.crop_mismatch_threshold:
            return Prediction(
                disease="Invalid Scan - Retake Photo",
                confidence=confidence,
                class_id=class_id,
                uncertain=True,
                top_predictions=filtered_top_predictions,
                rejected=True,
                rejection_reason=f"Low confidence for selected crop '{selected_crop}'. Please confirm crop selection and retake.",
            )

        if uncertain:
            disease = self.uncertain_label
        return Prediction(
            disease=disease,
            confidence=confidence,
            class_id=class_id,
            uncertain=uncertain,
            top_predictions=filtered_top_predictions,
            rejected=False,
            rejection_reason=None,
        )

    def info(self) -> dict:
        return {
            "model_loaded": self._model_loaded,
            "model_path": self.model_path,
            "class_count": len(self.class_names),
            "confidence_threshold": self.confidence_threshold,
            "uncertain_label": self.uncertain_label,
            "supported_crops": self.supported_crops,
        }
