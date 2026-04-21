# Agri Scan Backend

FastAPI service for crop disease prediction.

## Quick Start

1. Create a virtual environment and activate it.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy env template:
   - `copy .env.example .env`
4. Start API:
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Endpoints

- `GET /health`
- `POST /predict` (multipart/form-data, key: `file`)

## Dataset

Run:

- `python scripts/download_dataset.py`
- `python scripts/prepare_dataset.py`

This uses KaggleHub and downloads `emmarex/plantdisease`.

## Training

Run:

- `python train.py`

Outputs:

- `artifacts/final_model.keras`
- `artifacts/best_model.keras`
- `artifacts/class_names.txt`

## Notes

- Current `ModelService` contains deterministic fallback inference for development.
- Replace `ModelService._predict_stub` with TensorFlow model loading + inference once trained weights are available.
- Confidence guardrail is controlled by:
  - `CONFIDENCE_THRESHOLD`
  - `UNCERTAIN_LABEL`
