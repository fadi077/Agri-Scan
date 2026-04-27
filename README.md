# Agri Scan

Agri Scan is a crop leaf disease detector with a Next.js frontend and a FastAPI backend.

## Environment Setup

### Required versions

- Python: `3.10` (recommended `3.10.x`)
- Node.js: `18+` (tested with Node `22.x`)
- npm: `9+`

### System dependencies

- Git
- Webcam/browser permission for camera scanning
- Internet access (for `npm install` / `pip install`)

### Backend virtual environment (recommended)

From repo root:

1. `cd backend`
2. `python -m venv .venv`
3. Activate:
   - PowerShell: `.\.venv\Scripts\Activate.ps1`
   - CMD: `.venv\Scripts\activate.bat`
4. `python -m pip install --upgrade pip`
5. `pip install -r requirements.txt`
6. `cd ..`

### Frontend environment

1. `npm install`
2. `copy .env.example .env.local`

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

If you already split data into `train/`, `val/`, and `test/`, set `--data-dir` to the **parent** folder (for example `..\\data\\processed`) so validation and true test accuracy are both reported. If you have only one `train/` folder of classes, you can also point directly at that folder (the script will create a stratified val split from it).

For a faster smoke / A/B comparison on huge datasets, you can downsample the splits, e.g. ` --subsample-train 2000 --subsample-val 800 --subsample-test 800` (0 disables; omit the flags to use the full sets). Subsampled runs are **not** a substitute for a full final training when you are picking weights for the API.

**Full final training (recommended for deployment)** — from `backend` (tune `epochs` as needed, defaults are reasonable):

- `python -u scripts/train.py --data-dir "..\\data\\processed" --out-dir "..\\artifacts" --epochs 12`

That creates:

- `artifacts/best.pt`
- `artifacts/class_names.json`
- `artifacts/metrics.json` (per-epoch history + val/test accuracy + macro F1 + confusion matrix)

Restart backend after training. If these files are missing, `/predict` returns `503`.

## API

- `GET /health`
- `GET /model-info`
- `POST /predict` (`multipart/form-data`, field: `file`)

## Safety

- AI output is assistive guidance only.
- Always verify before treatment decisions.

