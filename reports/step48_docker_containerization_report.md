# Step 48: Docker Containerization & Production Packaging Report

## Executive Summary

**Project:** Gold Price Intelligence — Gold Price Prediction System during Diwali 2026  
**Step:** 48 — Docker Containerization & Production Packaging  
**Status:** HISTORICAL / DEPRECATED (Replaced by Step 48.1 — Direct Venv / Vite Workflow)  
**Date:** 2026-09-04  

> [!NOTE]
> **Historical / Deprecated**: As of Step 48.1, Docker containerization is deprecated for this project. The project runs directly via Python virtual environment (FastAPI/Uvicorn) and Node.js (React/Vite). This report is retained solely for historical project documentation.

---

## Container Architecture

```
[ Web Browser (Client) ]
       │
       ├───────────────────────────────┐
       ▼ (Port 80)                     ▼ (Port 8000)
┌──────────────────────────────┐  ┌──────────────────────────────┐
│  Frontend Container (Nginx)  │  │   Backend Container (FastAPI)│
│  - React / Vite Static Bundle│  │   - Uvicorn ASGI Server      │
│  - SPA Routing (nginx.conf)  │  │   - Read-only ML Artifacts   │
└──────────────────────────────┘  └──────────────────────────────┘
```

1. **Frontend Container (`gold_price_frontend`)**:
   - Multi-stage build (`node:20-alpine` → `nginx:alpine`).
   - Serves minified production static assets via Nginx on port `80`.
   - Includes Single Page Application (SPA) routing fallback handling deep URLs (`try_files $uri $uri/ /index.html`).

2. **Backend Container (`gold_price_backend`)**:
   - Production Python container (`python:3.11-slim`).
   - Serves read-only REST API endpoints on port `8000` via Uvicorn.
   - Includes production health check (`HEALTHCHECK`) targeting `GET /health`.

---

## Docker Artifacts Created

| Path / File | Purpose | Key Features / Configurations |
| :--- | :--- | :--- |
| **`Dockerfile.backend`** | Backend service image definition | `python:3.11-slim`, installs `requirements.txt`, copies `api/`, `models/`, `data/`, `reports/`, `src/`, exposes port `8000`, runs `python -m uvicorn api.main:app --host 0.0.0.0 --port 8000`. |
| **`Dockerfile`** | Root alias for backend service | Identical build configuration for standard `docker build .` execution. |
| **`frontend/Dockerfile`** | Frontend multi-stage image definition | **Stage 1 (build):** `node:20-alpine`, runs `npm ci` & `npm run build` with `ARG VITE_API_BASE_URL`.<br>**Stage 2 (runtime):** `nginx:alpine`, copies built `dist` to `/usr/share/nginx/html`. |
| **`frontend/nginx.conf`** | Nginx HTTP server block configuration | Serves static assets on port `80`, configures `try_files` for React Router support, defines standard error pages. |
| **`docker-compose.yml`** | Multi-container orchestration specification | Orchestrates `backend` and `frontend` services, configures port mapping (`80:80`, `8000:8000`), sets environment variables, configures container health dependencies. |
| **`compose.yml`** | Modern Docker CLI compose specification | Alias specification for `docker compose` compatibility. |
| **`.dockerignore`** | Root Docker context exclusions | Excludes `.git`, `.venv/`, `__pycache__`, `*.pyc`, `frontend/node_modules`, `frontend/dist`, `.env`, and log files from build context. |
| **`frontend/.dockerignore`** | Frontend context exclusions | Excludes `node_modules/`, `dist/`, `.env`, and log files. |

---

## Browser Access vs Container Networking

- When the frontend executes inside the browser, API requests originate from the **user's client web browser**, not from inside the Docker container network.
- Therefore, `VITE_API_BASE_URL` is set to `http://localhost:8000` (or the host's public IP/domain), ensuring the client browser can reach the published backend port `8000`.
- Docker container networking internal hostnames (`http://backend:8000`) are not used for browser-facing API configuration.

---

## Critical Protection & Invariant Verification

In strict compliance with project protection rules:

| Invariant / Constraint | Status | Verified Value / Behavior |
| :--- | :--- | :--- |
| **Model Retraining** | **NONE** | Existing model binaries untouched (`models/*.joblib`) |
| **Forecast Modification** | **NONE** | Frozen reference forecast strictly preserved |
| **Frozen Forecast Value** | **UNTOUCHED** | **₹142,442.41 per 10g** (Diwali 2026-11-08) |
| **Estimated Range** | **UNTOUCHED** | **₹137,889.90 — ₹144,859.72 per 10g** |
| **Selected Model** | **UNTOUCHED** | **Linear Regression** |
| **Test Performance** | **UNTOUCHED** | **MAE:** ₹2,122.61, **RMSE:** ₹2,576.56, **MAPE:** 1.41778%, **R²:** 0.840884 |
| **API Response Structure** | **UNTOUCHED** | Endpoints return exact schema and types |

---

## Verification Results

1. **Automated Pytest Suite**:
   ```
   python -m pytest -q
   ======================== 27 passed in 5.83s ========================
   ```

2. **Frontend Production Build**:
   ```
   npm run build (in frontend/)
   ✓ built in 1.08s
   dist/index.html                   0.65 kB
   dist/assets/index-BuWEJOTe.css   29.42 kB
   dist/assets/index-CfsIyEzp.js   675.40 kB
   ```

3. **Requirements UTF-8 Verification**:
   - Converted `requirements.txt` to clean UTF-8 text, eliminating Windows UTF-16 BOM characters for seamless `pip install` inside Linux Docker containers.

---

## Final Status

**COMPLETED** — The project is fully containerized, reproducible, and ready for containerized production deployment.
