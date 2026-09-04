# Gold Price Intelligence — Diwali 2026 Prediction System

## Environment Configuration

The application uses environment-based configuration for seamless local development and production deployment.

### Backend Configuration

- Local development file: `.env` (Ignored by Git)
- Template file: `.env.example` (Tracked in Git)

Example `.env` configuration:
```env
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

In production, environment variables (`ENVIRONMENT=production`, `CORS_ORIGINS=https://your-domain.com`) should be injected directly via host environment parameters or container settings.

### Frontend Configuration

- Local development file: `frontend/.env` (Ignored by Git)
- Template file: `frontend/.env.example` (Tracked in Git)

Example `frontend/.env`:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

> **Security Note:** Vite environment variables prefixed with `VITE_` are embedded into the client-side JavaScript build and visible to browser clients. Do not store secret keys in `VITE_` variables.

## Running Locally

### Backend (FastAPI)

```powershell
uvicorn api.main:app --reload
```

Interactive API documentation: http://127.0.0.1:8000/docs

Primary API Endpoints:
- `GET /health` — Liveness check
- `GET /ready` — Production artifact readiness check
- `GET /api/model-info` — Trained model metadata & evaluation metrics
- `GET /api/model-comparison` — Comparative metrics across 4 models
- `GET /api/diwali-prediction` — Frozen Diwali 2026 reference estimate
- `GET /api/weight-prediction?weight=N` — Proportional Diwali 2026 forecast for specified weight (1g to 15g)
- `GET /api/forecast` — Full business-day recursive forecast series
- `GET /api/historical-data` — Historical IBJA Gold 999 observations
- `GET /api/prediction-drivers` — Linear Regression feature contribution breakdown
- `GET /api/what-if` — Predefined market sensitivity scenario analysis

### Gold Weight Price Prediction

The core Machine Learning model predicts the Gold 999 price per 10 grams. The application provides an interactive Gold Weight Price Calculator allowing users to obtain equivalent predicted prices and confidence intervals for weights from 1g to 15g.

### Frontend (React / Vite)

```powershell
cd frontend
npm run dev
```

## Local & Production Deployment Workflow

### 1. Virtual Environment & Backend Setup

Activate the Python virtual environment and start the FastAPI ASGI server:

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run development server with auto-reload
python -m uvicorn api.main:app --reload
```

Production backend startup:
```powershell
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

Navigate to the frontend directory, install dependencies, and start the React / Vite development server:

```powershell
cd frontend
npm install
npm run dev
```

Production frontend build:
```powershell
cd frontend
npm run build
```

