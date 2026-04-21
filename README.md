# Agri Scan

Agri Scan is an AI-powered crop disease detection web app with:

- Next.js frontend (camera-first user flow)
- FastAPI backend for inference
- Structured dataset workflow for PlantVillage/Kaggle data

## Monorepo Structure

- `app`, `components`, `lib`: Next.js frontend
- `backend/app`: FastAPI API service
- `backend/scripts`: data and utility scripts

## Frontend Setup

1. Install dependencies:
   - `npm install`
2. Configure frontend env:
   - `copy .env.example .env.local`
3. Run frontend:
   - `npm run dev`
4. Open:
   - `http://localhost:3000`

## Backend Setup

1. Move into backend:
   - `cd backend`
2. Create venv and activate it.
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Configure backend env:
   - `copy .env.example .env`
5. Run backend:
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Dataset Download

Inside `backend`:

- `python scripts/download_dataset.py`

This downloads:

- `emmarex/plantdisease`

## API Contract

- `POST /predict`
  - `multipart/form-data`
  - field name: `file`
  - accepts `image/jpeg` and `image/png`
  - response:
    - `disease` (string)
    - `confidence` (0.0 to 1.0)
    - `class_id` (int)

## Safety

The frontend includes explicit safety disclaimers:

- AI output is assistive guidance only
- users should verify before pesticide application
- low-confidence outputs should be re-scanned and reviewed by an expert
