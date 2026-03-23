# RxShield

AI-powered prescription safety platform for detecting medication risk in typed or handwritten prescriptions.

RxShield combines:
- A React frontend for upload/review workflows
- A Node.js backend for auth, orchestration, and audit logging
- A FastAPI ML service for OCR + clinical risk analysis (DDI, dosage, LASA, allergies)

---

## 1) Production Overview

### Core capabilities
- Prescription OCR from images (Gemini Vision primary, Tesseract fallback)
- Structured drug extraction from OCR text
- Risk analysis with rules + ML checks
- LASA (look-alike/sound-alike) safety detection
- Firebase-authenticated APIs and audit logging

### Runtime architecture
```
Frontend (Vite/React)  --->  Backend API (Express)  --->  ML API (FastAPI)
				|                            |                        |
		Firebase Auth               Firestore logs         OCR + NER + Rules
```

### Service defaults
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:5000`
- ML API: `http://localhost:8000`

---

## 2) Tech Stack

- **Frontend:** React 19, Vite 7, Tailwind 4, Firebase client SDK
- **Backend:** Node.js 18+, Express 5, Firebase Admin SDK, Multer, Axios
- **ML Service:** FastAPI, Uvicorn, scikit-learn, Transformers, Pillow, OpenCV, pytesseract, Gemini API

---

## 3) Production-Safe Prerequisites

- Node.js `>=18`
- Python `>=3.10` (3.11 recommended)
- Tesseract OCR installed on runtime hosts (required for OCR fallback)
- Firebase project + service account credentials
- Gemini API key

### Tesseract on Windows
Install Tesseract and set the executable path in `ml-service/.env`:

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

> RxShield now auto-resolves Tesseract from:
> 1. `TESSERACT_CMD`
> 2. system `PATH`
> 3. common Windows install locations

---

## 4) Environment Configuration

Create env files from examples:
- `backend/.env` from `backend/.env.example`
- `frontend/.env` from `frontend/.env.example`
- `ml-service/.env` from `ml-service/.env.example`

### Backend (`backend/.env`)
Required:
- `PORT` (e.g., `5000` local, `3000` production)
- `NODE_ENV` (`development` or `production`)
- `ML_API_URL` (e.g., `http://localhost:8000`)
- `FRONTEND_URL` (frontend origin for CORS)
- `FIREBASE_PROJECT_ID`
- `FIREBASE_CLIENT_EMAIL`
- `FIREBASE_PRIVATE_KEY` (keep quotes + literal `\n` newlines)

### Frontend (`frontend/.env`)
Required:
- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`

API URL variables used by current code:
- `VITE_NODE_API_URL` (defaults to `http://localhost:5000`)
- `VITE_ML_API_URL` (defaults to `http://localhost:8000`, mainly for ML health checks)

### ML Service (`ml-service/.env`)
Required:
- `GEMINI_API_KEY`

Recommended:
- `GEMINI_MODEL` (e.g., `gemini-2.0-flash`)
- `GEMINI_FALLBACK_MODELS` (comma-separated model list)
- `TESSERACT_CMD` (strongly recommended on Windows/production)
- `PORT` (defaults to `8000`)

---

## 5) Local Development Runbook

Run all 3 services in separate terminals.

### A) Backend
```bash
cd backend
npm install
npm run dev
```

### B) Frontend
```bash
cd frontend
npm install
npm run dev
```

### C) ML Service
```bash
cd ml-service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 6) Health Checks

- Backend health: `GET http://localhost:5000/health`
- ML health: `GET http://localhost:8000/health`

Expected:
- Backend reports `status: ok`
- ML API reports loaded/lazy model status

---

## 7) API Flow (OCR + Analysis)

Primary endpoint used by frontend:
- `POST /api/ocr/analyze` (multipart image + optional patientData)

Backend flow:
1. Validates Firebase token
2. Sends image to ML `/ocr`
3. Sends structured OCR drugs to ML `/analyze-from-ocr`
4. Returns merged OCR + safety analysis payload

---

## 8) OCR Reliability Improvements (Implemented)

Current production OCR behavior includes:
- Gemini model is configurable via env (`GEMINI_MODEL`)
- Automatic Gemini fallback model attempts (`GEMINI_FALLBACK_MODELS`) when model is unavailable
- Robust Tesseract path discovery and explicit runtime checks
- Clear actionable errors when Tesseract is missing/misconfigured
- Drug extraction fallback chain now continues safely:
	- structured OCR drugs
	- NER extraction from cleaned text
	- regex extraction
	- fuzzy matching

Result: `structuredDrugs` can still be populated even when NER fails.

---

## 9) Frontend UX Fix (Implemented)

In OCR upload progress, final "Report Ready" now shows completed state (green tick) when process reaches done state, instead of remaining in loading spinner.

---

## 10) Troubleshooting

### `OCR failed ... tesseract.exe is not installed`
- Install Tesseract on host
- Set `TESSERACT_CMD` in `ml-service/.env`
- Restart ML API

### Gemini errors (`404 model not found` / `429 quota`)
- Set a valid `GEMINI_MODEL`
- Configure fallback list in `GEMINI_FALLBACK_MODELS`
- Verify API key/quota in Gemini project

### Backend returns `ML API is not running`
- Confirm ML service is running on `ML_API_URL`
- Check backend env value and restart backend

### `structuredDrugs` empty for unclear images
- Ensure latest ML service code is running (restart after changes)
- Improve image clarity (focus, lighting, crop)
- Confirm fallback stack logs (NER/regex/fuzzy)

---

## 11) Deployment Notes

- Backend includes CORS allowlist and supports production origin via `FRONTEND_URL`
- Keep secrets only in deployment env stores (Railway/Vercel dashboards), never in Git
- For stable OCR in production, install Tesseract on ML runtime even if Gemini is primary
- Scale ML API separately from frontend/backend due to heavier OCR + model workloads

---

## 12) Security Checklist

- [ ] Rotate exposed credentials immediately if any real secrets were committed
- [ ] Use least-privilege Firebase service account
- [ ] Restrict CORS to trusted frontend origin(s) in production
- [ ] Store env vars in platform secret manager
- [ ] Enforce HTTPS at edge/load balancer

---

## 13) Repository Structure

```
rxshield/
├── backend/         # Express API, auth middleware, OCR/analyze routing
├── frontend/        # React app (Vite)
├── ml-service/      # FastAPI + OCR + ML/rules engine
├── streamlit_app.py # Optional single-process demo app
└── README.md
```

---

## License

See `LICENSE`.
