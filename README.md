# Gold Price Intelligence — Gold Price Prediction System during Diwali 2026

A production-grade Financial Machine Learning & Market Intelligence Platform designed to predict India Bullion and Jewellers Association (IBJA) Gold 999 prices leading up to **Diwali 2026 (08 November 2026)**.

The system combines a multi-model econometric and machine learning pipeline with a high-performance **FastAPI** backend and an institutional-grade **React / Vite** financial analytics frontend.

---

## Executive Summary

| Metric / Parameter | Value |
| :--- | :--- |
| **Target Asset** | IBJA Gold 999 (24 Karat Fine Gold) |
| **Target Unit** | Indian Rupees (INR) per 10 grams |
| **Diwali Reference Date** | 2026-11-08 (Sunday) |
| **Selected Model** | **Linear Regression** |
| **Frozen Diwali Prediction** | **₹142,442.41 per 10g** |
| **Forecast Range (5th–95th %ile)** | **₹137,889.90 – ₹144,859.72 per 10g** |
| **Test Set MAE** | **₹2,122.61** |
| **Test Set RMSE** | **₹2,576.56** |
| **Test Set MAPE** | **1.4178%** |
| **Test Set R²** | **0.840884** |

---

## Project Overview

Physical gold holds immense cultural and financial significance in India, experiencing peak retail demand during the festive season of Diwali. Rapid shifts in macroeconomic variables—such as international spot gold prices (USD/oz) and the USD/INR exchange rate—create substantial price volatility for retail buyers, jewelers, and institutional investors.

This project delivers an end-to-end predictive analytics system that:
1. Ingests published IBJA market rates and exogenous global market signals.
2. Engineers 46 time-series and market proxy features.
3. Evaluates four machine learning architectures on a strict chronological split.
4. Generates a multi-step recursive business-day forecast from September 2026 through Diwali 2026.
5. Provides interactive explainability (Prediction Drivers), scenario sensitivity (What-If Analysis), and weight conversion (1g to 15g).

---

## Problem Statement

Predicting domestic gold prices in India presents several unique technical challenges:
- **Exogenous Currency & Commodity Coupling:** Domestic gold prices in INR are driven by international spot gold prices (USD/oz) multiplied by the USD/INR exchange rate, plus import duties and local taxes.
- **Non-Contiguous Trading Calendar:** Official market rates published by the IBJA omit weekends and national holidays.
- **Recursive Multi-Step Horizon:** Forecasting over a 49-business-day horizon requires multi-step recursive feature updates without introducing lookahead data leakage.

---

## Objectives

- Ingest historical IBJA Gold 999 observations and align them with international commodity and currency data.
- Enforce strict chronological train/validation/test splitting to respect time-series causality.
- Train and compare multiple ML models (Linear Regression, Random Forest, Gradient Boosting, XGBoost).
- Freeze the primary model's forecast for Diwali 2026 and serve it via a production FastAPI REST backend and React web application.

---

## Key Features

1. **Spot Market Intelligence Dashboard:** Real-time metrics, historical vs. forecast trend visuals, and IBJA rate indicators.
2. **Chronological Forecast Desk:** 49-business-day recursive projection series through Diwali 2026.
3. **Gold Weight Price Calculator (1g – 15g):** Interactive tool for converting 10g baseline predictions to any custom weight (1.0g to 15.0g).
4. **Prediction Drivers (Explainable AI):** Mathematical breakdown of Linear Regression coefficients and feature contributions.
5. **What-If Scenario Analysis:** Predefined sensitivity simulations testing market shifts in international gold ($\pm 5\%$) and USD/INR ($\pm 2\%$).
6. **Data Transparency & Methodology Checklist:** Independent verification panel confirming chronological integrity and zero target leakage.
7. **Model Lab & Performance Comparison:** Detailed evaluation benchmarks across candidate algorithms.

---

## System Architecture

The platform uses a decoupled client-server architecture:

```
┌─────────────────────────────────────────────────────────┐
│              React / Vite Web Frontend                  │
│  - Financial Dashboard, Forecast Desk, Weight Calc      │
│  - Recharts Visualisations, Lucide Icons, Vanilla CSS   │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP / JSON API
                             ▼
┌─────────────────────────────────────────────────────────┐
│                 FastAPI ASGI Backend                    │
│  - REST Endpoints, CORS Middleware, Error Handling       │
│  - Pydantic Validation, Artifact Ingestion              │
└────────────────────────────┬────────────────────────────┘
                             │ Read-Only Ingestion
                             ▼
┌─────────────────────────────────────────────────────────┐
│               Frozen ML Artifacts & Data                │
│  - models/linear_regression.joblib                      │
│  - models/final_diwali_forecast.json                    │
│  - data/processed/gold_master_dataset.csv               │
└─────────────────────────────────────────────────────────┘
```

---

## Machine Learning Workflow

```
[ IBJA PDF & Market Data ] ──► [ Master Dataset Assembly ] ──► [ 46 Feature Engineering ]
                                                                       │
[ Recursive Forecast Engine ] ◄── [ Chronological Evaluation ] ◄─── [ Train / Val / Test Split ]
```

1. **Ingestion:** Parse published IBJA quotes and fetch Yahoo Finance spot market feeds (`GC=F` and `USDINR=X`).
2. **Preprocessing:** Compute daily average target (`gold_999_avg`) in INR per 10g.
3. **Feature Construction:** Build 46 predictor features including target lags, rolling averages, volatility, returns, and market proxies.
4. **Partitioning:** Split chronologically into Train (117 rows), Validation (25 rows), and Test (26 rows).
5. **Training & Selection:** Train candidate models; select **Linear Regression** based on validation RMSE.
6. **Recursive Forecasting:** Multi-step recursive projection step-by-step into the future horizon.

---

## Data Sources

- **Primary Target Data:** India Bullion and Jewellers Association (IBJA) — Morning (AM) and Evening (PM) Gold 999 quotes (`data/raw/ibja_gold_999_2025_2026.csv`).
- **International Spot Gold:** Yahoo Finance spot gold closing prices in USD per troy ounce (`GC=F`).
- **Currency Exchange Rate:** Yahoo Finance USD/INR spot exchange rates (`USDINR=X`).

---

## Dataset Description & Limitations

- **Target Variable:** `target_gold_999` (Daily mathematical average of IBJA AM and PM quotes in INR per 10 grams).
- **Master Dataset Observations:** 168 unique business-day observations (`data/processed/gold_master_dataset.csv`).
- **Date Range:** 2025-09-02 to 2026-09-01.
- **Calendar Coverage:** 64.12% of weekday candidates across the 365-day calendar span.

### Important Data Limitation Notice
> **Note on Calendar Coverage:** The dataset consists strictly of published IBJA trading days. The IBJA does not publish market rates on weekends or central-government bank holidays. Missing calendar dates represent official market closures and were **not** artificially interpolated or fabricated into the target series.

---

## Feature Engineering

The system generates **46 predictor features** across 9 domain categories:

1. **Calendar Features (10):** `day_of_week`, `day_of_month`, `month`, `quarter`, `day_of_year`, `week_of_year`, `is_month_start`, `is_month_end`, `days_to_diwali`, `is_near_diwali`.
2. **Historical Target Lags (6):** `gold_lag_1`, `gold_lag_2`, `gold_lag_3`, `gold_lag_5`, `gold_lag_7`, `gold_lag_14` (shifted by $t-1$).
3. **Target Moving Averages (4):** `gold_ma_3`, `gold_ma_7`, `gold_ma_14`, `gold_ma_30`.
4. **Target Volatility Indicators (3):** `gold_volatility_7`, `gold_volatility_14`, `gold_volatility_30`.
5. **Target Percentage Returns (3):** `gold_return_1d`, `gold_return_3d`, `gold_return_7d`.
6. **International Market Features (9):** Spot gold OHLCV, 1d/3d/7d returns, and 7d/14d volatility.
7. **USD/INR Exchange Features (9):** Exchange rate OHLC, 1d/3d/7d returns, and 7d/14d volatility.
8. **Derived Market Proxy (1):** `gold_inr_proxy` (`gold_usd_close × usdinr_close`).
9. **Diwali Proximity Indicators (1):** Proximity distance metric.

---

## Train / Validation / Test Methodology

To preserve time-series causality, random shuffling was strictly prohibited.

- **Training Set (117 observations):** 2025-09-02 to 2026-06-19
- **Validation Set (25 observations):** 2026-06-22 to 2026-07-27
- **Holdout Test Set (26 observations):** 2026-07-28 to 2026-09-01
- **Preprocessing Fitting:** Preprocessing transformers (`SimpleImputer(strategy='median')`) were fitted exclusively on the Training Set.

---

## Model Comparison

Four algorithms were evaluated on the chronological validation set:

| Model | Validation MAE (₹) | Validation RMSE (₹) | Validation MAPE (%) | Validation R² | Selection Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Linear Regression** | **₹2,495.98** | **₹2,738.80** | **1.7459%** | **-1.3225** | **SELECTED** |
| **XGBoost Regressor** | ₹6,524.20 | ₹6,832.94 | 4.5660% | -13.4562 | Evaluated |
| **Gradient Boosting Regressor** | ₹9,385.52 | ₹9,657.06 | 6.5643% | -27.8754 | Evaluated |
| **Random Forest Regressor** | ₹9,847.32 | ₹10,091.01 | 6.8922% | -30.5288 | Evaluated |

---

## Final Model Performance

Selected **Linear Regression** performance on the completely untouched holdout test set (26 observations):

- **Mean Absolute Error (MAE):** **₹2,122.61**
- **Root Mean Squared Error (RMSE):** **₹2,576.56**
- **Mean Absolute Percentage Error (MAPE):** **1.4178%**
- **Coefficient of Determination (R²):** **0.840884**

---

## Diwali 2026 Forecast

- **Reference Date:** 2026-11-08 (Diwali)
- **Frozen Reference Estimate:** **₹142,442.41 per 10 grams**
- **Estimated Range (5th–95th %ile):** **₹137,889.90 – ₹144,859.72 per 10 grams**
- **Previous Business Day (2026-11-06):** ₹142,180.23 per 10g
- **Next Business Day (2026-11-09):** ₹142,704.58 per 10g

---

## Gold Weight Price Calculator (1g to 15g)

The platform provides an interactive weight converter allowing users to calculate predicted Gold 999 prices for any weight from 1.0g to 15.0g.

$$\text{price\_for\_weight} = \left(\frac{\text{price\_per\_10g}}{10.0}\right) \times \text{requested\_weight}$$

*Note: The weight conversion is a mathematical scaling layer resting on the frozen 10g ML baseline, not a separate machine learning model.*

---

## Prediction Drivers (Explainable AI)

The prediction for Diwali 2026 is decomposed into individual feature contributions using the fitted Linear Regression equation:

$$\hat{y} = \beta_0 + \sum_{i=1}^{p} \beta_i x_i$$

Top positive and negative drivers (e.g. `gold_inr_proxy`, `gold_ma_30`, `usdinr_close`) are displayed with exact raw values, transformed metrics, coefficients, and net contribution values.

---

## What-If Scenario Analysis

The system provides predefined market sensitivity simulations:

| Market Scenario | Adjustment | Diwali 2026 Estimate (₹/10g) | Change (₹) | Change (%) |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline Forecast** | Unadjusted Market Inputs | **₹142,442.41** | ₹0.00 | 0.00% |
| **International Gold +5%** | Spot Gold +5% | ₹144,643.05 | +₹2,200.64 | +1.54% |
| **International Gold −5%** | Spot Gold −5% | ₹140,241.77 | -₹2,200.64 | -1.54% |
| **USD/INR +2%** | USD/INR +2% | ₹143,778.68 | +₹1,336.27 | +0.94% |
| **USD/INR −2%** | USD/INR −2% | ₹141,106.14 | -₹1,336.27 | -0.94% |

---

## Data Transparency & Methodology

- **No Future Actuals:** The recursive forecast engine uses projected exogenous inputs (`GC=F`, `USDINR=X`) and lag states.
- **Train-Only Scaling:** Preprocessors were fitted exclusively on training rows.
- **Frozen Artifact Protection:** Models and forecast JSONs remain static and immutable.

---

## FastAPI Backend Architecture

The backend (`api/main.py`) provides a robust REST API using FastAPI and Pydantic:
- CORS middleware configured via environment settings.
- Custom exception handling for HTTP 400/422 and 500 errors.
- Automatic root redirect (`GET /` $\to$ `/docs`).

---

## React / Vite Frontend Architecture

The frontend (`frontend/src/`) is a responsive Single Page Application (SPA):
- **Component Hierarchy:** `App.jsx`, `CombinedChart.jsx`, `GoldWeightCalculator.jsx`, `ModelComparison.jsx`, `PredictionDrivers.jsx`, `WhatIfAnalysis.jsx`, `RangeBar.jsx`, `DataIntegrityBadge.jsx`.
- **Styling:** CSS Custom Properties (Design Tokens), zero Tailwind dependency.

---

## API Endpoint Documentation

| Endpoint | Method | Response Model | Description |
| :--- | :--- | :--- | :--- |
| `GET /` | Redirect | `RedirectResponse` | Redirects to `/docs` OpenAPI UI |
| `GET /health` | GET | `HealthResponse` | Liveness health check |
| `GET /ready` | GET | `ReadinessResponse` | Production artifact availability check |
| `GET /api/model-info` | GET | `ModelInfoResponse` | Trained model metadata & evaluation metrics |
| `GET /api/model-comparison` | GET | `list[ModelComparisonPoint]` | Comparative metrics across 4 models |
| `GET /api/diwali-prediction` | GET | `DiwaliPredictionResponse` | Frozen Diwali 2026 reference estimate |
| `GET /api/weight-prediction` | GET | `WeightPredictionResponse` | Proportional forecast for weight (1g to 15g) |
| `GET /api/forecast` | GET | `list[ForecastPoint]` | Full business-day recursive forecast series |
| `GET /api/historical-data` | GET | `list[HistoricalPoint]` | Historical IBJA Gold 999 observations |
| `GET /api/prediction-drivers` | GET | `PredictionDriversResponse` | Linear Regression feature contribution breakdown |
| `GET /api/what-if` | GET | `WhatIfResponse` | Predefined market sensitivity scenario analysis |

---

## Project Folder Structure

```
Gold_Price_Prediction_2026/
├── api/                        # FastAPI Backend Application
│   ├── config.py               # Environment configuration
│   └── main.py                 # FastAPI routes & exception handlers
├── data/                       # Data Artifacts
│   ├── processed/              # Clean master & feature CSV datasets
│   └── raw/                    # Source IBJA PDFs & CSV feeds
├── frontend/                   # React / Vite Web Application
│   ├── src/
│   │   ├── components/         # React UI components
│   │   ├── services/           # API fetch helpers
│   │   ├── App.jsx             # Main SPA views & router
│   │   └── App.css             # Institutional CSS design tokens
│   ├── package.json            # Node dependencies
│   └── vite.config.js          # Vite build configuration
├── models/                     # Trained Model & Forecast Artifacts
│   ├── linear_regression.joblib
│   ├── final_diwali_forecast.json
│   └── model_metadata.json
├── reports/                    # Executive & Step Audit Reports
│   └── step48_2_weight_prediction_report.md
├── src/                        # Data & Modeling Scripts
│   ├── data/                   # Extraction & master dataset scripts
│   ├── features/               # Feature engineering scripts
│   └── models/                 # Model training & forecast engine
├── tests/                      # Pytest Automated Test Suite
│   ├── test_api.py
│   ├── test_weight_prediction.py
│   └── test_frontend_hardcode_check.py
├── .env.example                # Root environment template
├── pytest.ini                  # Pytest configuration
├── README.md                   # Project documentation
└── requirements.txt            # Python dependencies
```

---

## Installation & Prerequisites

### Prerequisites
- **Python:** Version 3.11 or higher
- **Node.js:** Version 18 or higher (with `npm`)

---

## Local & Production Deployment Workflow

### 1. Virtual Environment & Backend Setup

```powershell
# Activate Python virtual environment
.\.venv\Scripts\Activate.ps1

# Run FastAPI development server with reload
python -m uvicorn api.main:app --reload --port 8000
```

Production backend startup:
```powershell
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```powershell
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start React / Vite development server
npm run dev
```

Production frontend build:
```powershell
cd frontend
npm run build
```

---

## Testing Instructions

Execute the complete automated Pytest test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

*Expected Result:* **34 / 34 unit & integration tests passing.**

---

## Environment Configuration

### Backend Configuration (`.env`)
```env
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Frontend Configuration (`frontend/.env`)
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## Limitations

1. **Non-Contiguous Calendar:** IBJA quotes omit weekends and bank holidays.
2. **Exogenous Assumptions:** The forecast relies on independent projections for spot gold and USD/INR. Unexpected macroeconomic shocks or geopolitical events during September–November 2026 may impact actual prices.

---

## Future Improvements

- Incorporate GARCH volatility modeling for dynamic error bounds.
- Implement an automated PDF parser pipeline for real-time daily IBJA ingestion.
- Expand multi-currency spot market proxy options.

---

## License & Academic Disclaimer

This project is developed for academic evaluation and educational research purposes. Gold price predictions represent statistical model estimates and should not be construed as financial advice.
