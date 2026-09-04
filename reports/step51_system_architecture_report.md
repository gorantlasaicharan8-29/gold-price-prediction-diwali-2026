# Step 51 — System Architecture Documentation Report

## Executive Summary

**Project:** Gold Price Intelligence — Gold Price Prediction System during Diwali 2026  
**Step:** 51 — Professional System Architecture Diagram & Documentation  
**Status:** COMPLETED  
**Date:** 2026-09-04  

This report documents the architectural design and data flow of the completed **Gold Price Intelligence** platform. Both vector SVG (`reports/system_architecture.svg`) and high-resolution PNG (`reports/system_architecture.png`) visualization diagrams have been generated to document the system for project reports, HOD presentations, and repository documentation.

---

## Architectural Diagram Artifacts Created

1. **`reports/system_architecture.svg`**: Scalable Vector Graphics (SVG) architecture diagram featuring responsive vector shapes, crisp typography, and institutional financial design tokens.
2. **`reports/system_architecture.png`**: High-resolution PNG render (200 DPI, $3200 \times 5200$ effective resolution) ideal for slide decks, PDF reports, and GitHub README embeds.

---

## Architecture Overview

The platform uses a modular 8-layer architecture spanning offline machine learning pipeline operations, frozen artifact serving, high-performance REST API routing, and interactive frontend financial analytics.

```
┌───────────────────────────────────────────────────────────┐
│                 1. DATA SOURCES LAYER                     │
│    - IBJA Gold 999  │  Spot Gold (GC=F)  │  USD/INR       │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│          2. DATA PROCESSING & ALIGNMENT LAYER             │
│    - Parsing, Cleaning, Target Average, Master Alignment  │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│            3. FEATURE ENGINEERING LAYER (46)              │
│    - Target Lags, Moving Avg, Volatility, FX Proxies      │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│       4. TIME-AWARE CHRONOLOGICAL SPLIT LAYER             │
│    - Train (117)  │  Validation (25)  │  Test (26)       │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│      5. MODEL TRAINING & COMPARISON LAYER                 │
│    - Linear Regression (Selected), XGBoost, GB, RF        │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│     6. FROZEN DIWALI 2026 FORECAST & RECURSIVE ENGINE     │
│    - Reference Estimate: ₹142,442.41 per 10g              │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│              7. FASTAPI BACKEND REST API LAYER            │
│    - 11 Endpoints, CORS Middleware, Pydantic Validation   │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│      8. REACT / VITE FRONTEND ANALYTICS DASHBOARD LAYER   │
│    - Dashboard, Forecast Desk, Weight Calc (1g-15g)      │
└───────────────────────────────────────────────────────────┘
```

---

## Detailed Explanation of Architectural Layers

### Layer 1: Data Sources Layer
Handles ingestion from three independent financial data providers:
- **IBJA Gold 999:** Official physical market rates in INR per 10g (Morning AM and Evening PM quotes) spanning 168 business days (2025-09-02 to 2026-09-01).
- **International Spot Gold (`GC=F`):** Yahoo Finance global spot gold prices in USD per troy ounce.
- **USD/INR Exchange Rate (`USDINR=X`):** Yahoo Finance spot currency exchange rates.

### Layer 2: Data Processing & Alignment Layer
Converts raw inputs into a clean target series:
- Computes `target_gold_999 = (gold_999_am + gold_999_pm) / 2`.
- Aligns quotes on trade date key, producing `data/processed/gold_master_dataset.csv` (168 rows).

### Layer 3: Feature Engineering Layer
Constructs **46 predictor features** across 9 structured categories:
- Target Lags ($t-1 \dots t-14$), Target Moving Averages (3, 7, 14, 30 days), Target Volatility (7, 14, 30 days), Target Percentage Returns.
- Exogenous Spot Gold & USD/INR returns and volatility.
- Derived market proxy: `gold_inr_proxy` (`gold_usd_close × usdinr_close`).
- Festive calendar proximity: `days_to_diwali` and `is_near_diwali`.

### Layer 4: Time-Aware Chronological Split Layer
Enforces strict time-series causality without random shuffling:
- **Training Set (70%):** 117 observations (2025-09-02 to 2026-06-19). Preprocessing transformers (`SimpleImputer(strategy='median')`) are fitted exclusively on this split.
- **Validation Set (15%):** 25 observations (2026-06-22 to 2026-07-27) for hyperparameter selection.
- **Holdout Test Set (15%):** 26 observations (2026-07-28 to 2026-09-01) isolated as an untouched final benchmark.

### Layer 5: Model Training, Evaluation & Selection Layer
Trains and compares four machine learning algorithms on chronological validation RMSE:
- **Linear Regression:** Validation MAE = ₹2,495.98, RMSE = ₹2,738.80, MAPE = 1.7459% (**SELECTED**).
- **XGBoost Regressor:** Validation MAE = ₹6,524.20, RMSE = ₹6,832.94.
- **Gradient Boosting Regressor:** Validation MAE = ₹9,385.52, RMSE = ₹9,657.06.
- **Random Forest Regressor:** Validation MAE = ₹9,847.32, RMSE = ₹10,091.01.

### Layer 6: Frozen Diwali 2026 Forecast & Recursive Engine Layer
- **Selected Production Model:** Linear Regression
- **Holdout Test Metrics:** MAE = **₹2,122.61**, RMSE = **₹2,576.56**, MAPE = **1.4178%**, $R^2 = \mathbf{0.840884}$.
- **Frozen Reference Estimate:** **₹142,442.41 per 10 grams** for Diwali (2026-11-08).
- **Estimated Range (5th–95th %ile):** **₹137,889.90 – ₹144,859.72 per 10g**.

### Layer 7: FastAPI Backend REST API Layer
Serves frozen artifacts via 11 high-performance Python endpoints:
- System liveness & readiness: `GET /health`, `GET /ready`, `GET /` (Redirects to `/docs`).
- Forecast & weight scaling: `GET /api/diwali-prediction`, `GET /api/forecast`, `GET /api/weight-prediction?weight=N`.
- Model & Data: `GET /api/model-info`, `GET /api/model-comparison`, `GET /api/historical-data`.
- Explainability & Sensitivity: `GET /api/prediction-drivers`, `GET /api/what-if`.

### Layer 8: React / Vite Frontend Analytics Dashboard Layer
Interactive financial SPA built with React, Vite, Recharts, and Vanilla CSS design tokens:
- **Market Intelligence Dashboard:** Live ticker, observed target snapshot, forecast spotlight.
- **Forecast Desk:** Historical vs. forecast transition chart, 1g to 15g Gold Weight Calculator.
- **Model Lab & Explainability:** ModelComparison table, PredictionDrivers decomposition ($y = \beta_0 + \sum \beta_i x_i$), What-If market sensitivity scenarios, Data Integrity Badge.

---

## Confirmation of ML Artifact & Forecast Protection

- **ML Models & Artifacts:** **UNTOUCHED and UNCHANGED**. No models were retrained.
- **Selected Model:** **UNCHANGED** (Linear Regression).
- **Frozen Forecast Value:** **UNCHANGED** (₹142,442.41 per 10g).
- **Forecast Files:** `models/final_diwali_forecast.json` remained static.

---

## System Verification

- **Pytest Suite:** Executed `.\.venv\Scripts\python.exe -m pytest -q` $\to$ **34 / 34 tests passed**.
- **Frontend Build:** Executed `npm run build` in `frontend/` $\to$ **PASS (964ms)**.
