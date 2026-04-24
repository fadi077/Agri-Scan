# Agri Scan

Agri Scan is a crop leaf disease detector with a Next.js frontend and a FastAPI backend.

## Quick Start

1. Install frontend dependencies (repo root):
   - `npm install`
2. Install backend dependencies:
   - `cd backend`
   - `pip install -r requirements.txt`
3. Copy frontend env:
   - `copy ..\\.env.example ..\\.env.local`
4. Run both apps from repo root:
   - `cd ..`
   - `npm run dev:all`
5. Open:
   - `http://localhost:3000`

## Kaggle Model Workflow (Required)

This project now uses **local trained weights only** for predictions.

From `backend`, train on your Kaggle ImageFolder dataset:

- `python scripts/train.py --data-dir "<KAGGLE_IMAGEFOLDER_ROOT>" --out-dir ..\\artifacts`

That creates:

- `artifacts/best.pt`
- `artifacts/class_names.json`

Restart backend after training. If these files are missing, `/predict` returns `503`.

## API

- `GET /health`
- `GET /model-info`
- `POST /predict` (`multipart/form-data`, field: `file`)

## Safety

- AI output is assistive guidance only.
- Always verify before treatment decisions.

