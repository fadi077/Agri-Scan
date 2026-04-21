from __future__ import annotations

import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .model import ModelService
from .schemas import HealthResponse, ModelInfoResponse, PredictionResponse

app = FastAPI(title="Agri Scan API", version="1.0.0")
model_service = ModelService()

allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    model_service.load()


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse()


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    return ModelInfoResponse(**model_service.info())


@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...), crop: str = Form("any")) -> PredictionResponse:
    if not file.content_type or file.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=400, detail="Only JPEG and PNG images are supported.")

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(raw_bytes) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image exceeds 8MB size limit.")

    prediction = model_service.predict(raw_bytes, selected_crop=crop)
    return PredictionResponse(
        disease=prediction.disease,
        confidence=prediction.confidence,
        class_id=prediction.class_id,
        uncertain=prediction.uncertain,
        top_predictions=prediction.top_predictions or [],
        rejected=prediction.rejected,
        rejection_reason=prediction.rejection_reason,
        selected_crop=crop.lower().strip() if crop else "any",
    )
