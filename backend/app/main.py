"""FastAPI entrypoint: PyTorch inference from local trained weights only."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Annotated, Any

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from PIL import Image, UnidentifiedImageError

from app.config import (
    class_names_path,
    confidence_threshold,
    min_image_bytes,
    model_weight_path,
    prediction_margin_threshold,
    rejection_confidence_threshold,
    training_dataset_dir,
    user_uploads_dir,
)
from app.model import ClassifierRuntime, try_load_classifier
from app.upload_sink import persist_scan_upload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UNCERTAIN_LABEL = "Uncertain"
NO_MODEL_DETAIL = (
    "No trained model is loaded. This project is configured to use local Kaggle-trained weights only. "
    "From the `backend` folder run: `python scripts/train.py --data-dir <Kaggle_ImageFolder_root> --out-dir ..\\artifacts` "
    "to create `artifacts/best.pt` and `artifacts/class_names.json`, then restart the API."
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    w_path = model_weight_path()
    c_path = class_names_path()
    ct = confidence_threshold()
    mb = min_image_bytes()

    bundle = try_load_classifier(
        weights_path=w_path,
        class_names_path=c_path,
        confidence_threshold=ct,
        min_image_bytes=mb,
    )
    app.state.classifier = bundle
    if bundle is None:
        logger.warning("Classifier not loaded; /predict will return 503 until local weights exist.")
    else:
        display = getattr(bundle, "source", str(w_path))
        logger.info(
            "Loaded %s (%s classes, diagnostic_ready=%s) — %s",
            bundle.arch,
            bundle.class_count,
            getattr(bundle, "diagnostic_ready", True),
            display,
        )
    yield


app = FastAPI(title="Agri Scan API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/model-info")
def model_info(request: Request) -> dict[str, Any]:
    bundle: ClassifierRuntime | None = getattr(request.app.state, "classifier", None)
    w_path = model_weight_path()
    c_path = class_names_path()
    td = training_dataset_dir()
    uu = user_uploads_dir()
    if bundle is None:
        return {
            "model_loaded": False,
            "model_path": str(w_path),
            "class_count": 0,
            "confidence_threshold": confidence_threshold(),
            "uncertain_label": UNCERTAIN_LABEL,
            "supported_crops": ["tomato", "potato", "pepper", "any"],
            "class_names_path": str(c_path),
            "diagnostic_ready": False,
            "architecture": None,
            "training_dataset_dir": str(td) if td else None,
            "user_uploads_dir": str(uu),
        }
    return {
        "model_loaded": True,
        "model_path": str(w_path),
        "class_count": bundle.class_count,
        "confidence_threshold": bundle.confidence_threshold,
        "rejection_confidence_threshold": rejection_confidence_threshold(),
        "prediction_margin_threshold": prediction_margin_threshold(),
        "uncertain_label": UNCERTAIN_LABEL,
        "supported_crops": ["tomato", "potato", "pepper", "any"],
        "class_names_path": str(c_path),
        "diagnostic_ready": bool(getattr(bundle, "diagnostic_ready", True)),
        "architecture": getattr(bundle, "arch", "unknown"),
        "training_dataset_dir": str(td) if td else None,
        "user_uploads_dir": str(uu),
    }


def _guess_is_probably_image(data: bytes) -> bool:
    if len(data) < 8:
        return False
    if data[:2] == b"\xff\xd8":
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    return False


def _leaf_presence_gate(data: bytes) -> tuple[bool, str | None]:
    """
    Reject obviously non-leaf photos (hands, walls, desk) before disease inference.
    Uses a lightweight HSV green-ratio heuristic.
    """
    try:
        image = Image.open(BytesIO(data)).convert("RGB").resize((192, 192))
    except (UnidentifiedImageError, OSError, ValueError):
        return False, "Could not decode image content."

    arr = np.asarray(image, dtype=np.uint8)
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)

    # Green-biased mask with margin over red/blue to avoid neutral backgrounds.
    green_mask = (g > (r * 1.08)) & (g > (b * 1.08)) & ((g - r) > 12) & ((g - b) > 8) & (g > 40)
    h, w = green_mask.shape
    total = float(max(1, h * w))
    green_ratio = float(green_mask.sum()) / total

    if green_ratio < 0.08:
        return False, "No clear leaf area detected. Retake with a close, single leaf filling most of the frame."

    # Require some green in the center region so side/background green doesn't pass.
    cy0, cy1 = int(h * 0.25), int(h * 0.75)
    cx0, cx1 = int(w * 0.25), int(w * 0.75)
    center = green_mask[cy0:cy1, cx0:cx1]
    center_ratio = float(center.sum()) / float(max(1, center.size))
    if center_ratio < 0.05:
        return False, "Leaf is not centered or too small. Fill the center frame with one leaf."

    # Largest connected green component should be substantial (reject scattered speckles).
    visited = np.zeros_like(green_mask, dtype=bool)
    max_comp = 0
    for y in range(h):
        for x in range(w):
            if not green_mask[y, x] or visited[y, x]:
                continue
            stack = [(y, x)]
            visited[y, x] = True
            size = 0
            while stack:
                yy, xx = stack.pop()
                size += 1
                if yy > 0 and green_mask[yy - 1, xx] and not visited[yy - 1, xx]:
                    visited[yy - 1, xx] = True
                    stack.append((yy - 1, xx))
                if yy + 1 < h and green_mask[yy + 1, xx] and not visited[yy + 1, xx]:
                    visited[yy + 1, xx] = True
                    stack.append((yy + 1, xx))
                if xx > 0 and green_mask[yy, xx - 1] and not visited[yy, xx - 1]:
                    visited[yy, xx - 1] = True
                    stack.append((yy, xx - 1))
                if xx + 1 < w and green_mask[yy, xx + 1] and not visited[yy, xx + 1]:
                    visited[yy, xx + 1] = True
                    stack.append((yy, xx + 1))
            if size > max_comp:
                max_comp = size

    if (max_comp / total) < 0.04:
        return False, "No dominant leaf region found. Capture one clear leaf against a plain background."

    return True, None


@app.post("/predict")
async def predict(
    request: Request,
    file: Annotated[UploadFile, File(description="Leaf image (JPEG or PNG)")],
    crop: Annotated[str, Form()] = "any",
) -> dict[str, Any]:
    bundle: ClassifierRuntime | None = getattr(request.app.state, "classifier", None)
    if bundle is None:
        raise HTTPException(status_code=503, detail=NO_MODEL_DETAIL)

    if crop not in ("any", "tomato", "potato", "pepper"):
        raise HTTPException(status_code=400, detail="Invalid crop. Use any, tomato, potato, or pepper.")

    raw = await file.read()
    if len(raw) < min_image_bytes():
        out = {
            "disease": UNCERTAIN_LABEL,
            "confidence": 0.0,
            "class_id": -1,
            "uncertain": True,
            "rejected": True,
            "rejection_reason": "Image too small or empty. Please upload a clear leaf photo.",
            "top_predictions": [],
            "selected_crop": crop,
        }
        out.update(
            persist_scan_upload(
                raw,
                crop=crop,
                disease=None,
                class_id=-1,
                confidence=0.0,
                rejected=True,
                rejection_reason=out["rejection_reason"],
                uncertain=True,
            )
        )
        return out

    if not _guess_is_probably_image(raw):
        out = {
            "disease": UNCERTAIN_LABEL,
            "confidence": 0.0,
            "class_id": -1,
            "uncertain": True,
            "rejected": True,
            "rejection_reason": "Could not read a JPEG/PNG image. Try another file or capture from the camera.",
            "top_predictions": [],
            "selected_crop": crop,
        }
        out.update(
            persist_scan_upload(
                raw,
                crop=crop,
                disease=None,
                class_id=-1,
                confidence=0.0,
                rejected=True,
                rejection_reason=out["rejection_reason"],
                uncertain=True,
            )
        )
        return out

    looks_like_leaf, leaf_reason = _leaf_presence_gate(raw)
    if not looks_like_leaf:
        out = {
            "disease": UNCERTAIN_LABEL,
            "confidence": 0.0,
            "class_id": -1,
            "uncertain": True,
            "rejected": True,
            "rejection_reason": leaf_reason,
            "top_predictions": [],
            "selected_crop": crop,
        }
        out.update(
            persist_scan_upload(
                raw,
                crop=crop,
                disease=None,
                class_id=-1,
                confidence=0.0,
                rejected=True,
                rejection_reason=out["rejection_reason"],
                uncertain=True,
            )
        )
        return out

    try:
        out = bundle.predict(raw, crop)
    except ValueError as e:
        code = str(e)
        if code == "IMAGE_TOO_SMALL":
            out = {
                "disease": UNCERTAIN_LABEL,
                "confidence": 0.0,
                "class_id": -1,
                "uncertain": True,
                "rejected": True,
                "rejection_reason": "Image data was too small to analyze.",
                "top_predictions": [],
                "selected_crop": crop,
            }
            out.update(
                persist_scan_upload(
                    raw,
                    crop=crop,
                    disease=None,
                    class_id=-1,
                    confidence=0.0,
                    rejected=True,
                    rejection_reason=out["rejection_reason"],
                    uncertain=True,
                )
            )
            return out
        if code == "INVALID_IMAGE":
            out = {
                "disease": UNCERTAIN_LABEL,
                "confidence": 0.0,
                "class_id": -1,
                "uncertain": True,
                "rejected": True,
                "rejection_reason": "The file could not be decoded as an image.",
                "top_predictions": [],
                "selected_crop": crop,
            }
            out.update(
                persist_scan_upload(
                    raw,
                    crop=crop,
                    disease=None,
                    class_id=-1,
                    confidence=0.0,
                    rejected=True,
                    rejection_reason=out["rejection_reason"],
                    uncertain=True,
                )
            )
            return out
        if code == "IMAGE_TOO_SMALL_DIM":
            out = {
                "disease": UNCERTAIN_LABEL,
                "confidence": 0.0,
                "class_id": -1,
                "uncertain": True,
                "rejected": True,
                "rejection_reason": "Image resolution is too low; capture a larger leaf photo.",
                "top_predictions": [],
                "selected_crop": crop,
            }
            out.update(
                persist_scan_upload(
                    raw,
                    crop=crop,
                    disease=None,
                    class_id=-1,
                    confidence=0.0,
                    rejected=True,
                    rejection_reason=out["rejection_reason"],
                    uncertain=True,
                )
            )
            return out
        if code == "NO_CLASSES_FOR_CROP":
            raise HTTPException(
                status_code=400,
                detail="This model has no class labels that match the selected crop. Choose “Any Crop” or retrain with labels that include that crop.",
            ) from e
        raise HTTPException(status_code=500, detail="Unexpected inference error.") from e

    second_conf = out.top_predictions[1]["confidence"] if len(out.top_predictions) > 1 else 0.0
    margin = out.confidence - float(second_conf)
    if out.confidence < rejection_confidence_threshold() or margin < prediction_margin_threshold():
        out_body = {
            "disease": UNCERTAIN_LABEL,
            "confidence": out.confidence,
            "class_id": out.class_id,
            "uncertain": True,
            "rejected": True,
            "rejection_reason": (
                "Prediction is not reliable for supported crops. This image may belong to an unsupported crop "
                "(for example banana/peach) or be outside the model's training scope."
            ),
            "top_predictions": out.top_predictions,
            "selected_crop": crop,
        }
        out_body.update(
            persist_scan_upload(
                raw,
                crop=crop,
                disease=None,
                class_id=out.class_id,
                confidence=out.confidence,
                rejected=True,
                rejection_reason=out_body["rejection_reason"],
                uncertain=True,
            )
        )
        return out_body

    body: dict[str, Any] = {
        "disease": out.disease,
        "confidence": out.confidence,
        "class_id": out.class_id,
        "uncertain": out.uncertain,
        "top_predictions": out.top_predictions,
        "rejected": False,
        "rejection_reason": None,
        "selected_crop": crop,
    }
    body.update(
        persist_scan_upload(
            raw,
            crop=crop,
            disease=out.disease,
            class_id=out.class_id,
            confidence=out.confidence,
            rejected=False,
            rejection_reason=None,
            uncertain=out.uncertain,
        )
    )
    return body
