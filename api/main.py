"""FastAPI backend for the frozen Gold Price Prediction System."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from api.config import (
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    LOG_LEVEL,
    get_cors_origins,
)

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("gold_price_api")


# ─── Artifact paths ───────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_METADATA_PATH     = PROJECT_ROOT / "models" / "model_metadata.json"
FINAL_FORECAST_PATH     = PROJECT_ROOT / "models" / "final_diwali_forecast.json"
FORECAST_PATH           = PROJECT_ROOT / "data" / "processed" / "model_data" / "diwali_recursive_forecast.csv"
HISTORICAL_PATH         = PROJECT_ROOT / "data" / "processed" / "gold_master_dataset.csv"
VALIDATION_RESULTS_PATH = PROJECT_ROOT / "reports" / "model_evaluation" / "validation_results.csv"
PREDICTION_DRIVERS_PATH = PROJECT_ROOT / "models" / "prediction_drivers.json"
SENSITIVITY_PATH        = PROJECT_ROOT / "reports" / "diwali_sensitivity_analysis.csv"


# ─── Pydantic models ──────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]



class ModelInfoResponse(BaseModel):
    model: str
    validation: dict[str, float]
    test: dict[str, float]
    training_rows: int
    validation_rows: int
    test_rows: int
    feature_count: int


class BusinessDayForecast(BaseModel):
    date: str
    forecast: float


class EstimatedRange(BaseModel):
    lower: float
    upper: float


class DiwaliPredictionResponse(BaseModel):
    diwali_date: str
    previous_business_day: BusinessDayForecast
    diwali_reference_estimate: BusinessDayForecast
    next_business_day: BusinessDayForecast
    estimated_range: EstimatedRange
    unit: str
    model: str


class ForecastPoint(BaseModel):
    date: str
    forecast_gold_999: float
    gold_usd_close_forecast: float
    usdinr_close_forecast: float
    gold_inr_proxy: float
    days_to_diwali: int
    is_near_diwali: int


class HistoricalPoint(BaseModel):
    date: str
    gold_999_am: float
    gold_999_pm: float
    gold_999_avg: float
    target_gold_999: float
    gold_usd_close: float | None = None
    usdinr_close: float | None = None


class ModelComparisonPoint(BaseModel):
    model: str
    MAE: float
    RMSE: float
    MAPE: float
    R2: float
    selected: bool


class DriverItem(BaseModel):
    feature: str
    display_name: str
    raw_value: float | None = None
    transformed_value: float
    coefficient: float
    contribution: float
    absolute_contribution: float
    direction: str


class PredictionDriversResponse(BaseModel):
    model: str
    forecast_date: str
    prediction: float
    intercept: float
    total_positive_contribution: float
    total_negative_contribution: float
    top_positive_drivers: list[DriverItem]
    top_negative_drivers: list[DriverItem]
    positive_drivers: list[DriverItem]
    negative_drivers: list[DriverItem]
    reconstruction_status: str


class WhatIfScenario(BaseModel):
    scenario: str
    display_name: str
    gold_market_adjustment: float
    usdinr_adjustment: float
    prediction: float
    change: float
    change_percentage: float
    market_assumption: str
    is_baseline: bool


class WhatIfResponse(BaseModel):
    baseline_prediction: float
    scenarios: list[WhatIfScenario]


class WeightPredictionResponse(BaseModel):
    weight_grams: float
    price_per_10g: float
    price_per_gram: float
    predicted_price: float
    lower_estimate: float | None = None
    upper_estimate: float | None = None
    currency: str
    unit: str
    reference_date: str
    model: str


# ─── App ──────────────────────────────────────────────────────────────────────

tags_metadata = [
    {"name": "Health", "description": "API liveness check."},
    {"name": "Readiness", "description": "Production readiness & artifact availability check."},
    {"name": "Model", "description": "Trained model metadata and evaluation benchmarks."},
    {"name": "Forecast", "description": "Diwali 2026 reference estimate and recursive forecast series."},
    {"name": "Historical Data", "description": "Historical IBJA Gold 999 observations."},
    {"name": "Explainability", "description": "Linear Regression feature contributions and driver analysis."},
    {"name": "What-If Analysis", "description": "Predefined market sensitivity scenarios."},
]

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ─── Exception Handlers ───────────────────────────────────────────────────────

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


# ─── Artifact helpers ─────────────────────────────────────────────────────────

def read_json_artifact(path: Path) -> dict[str, Any]:
    """Load a JSON file and raise a clean HTTP 500 if it is missing or corrupt."""
    if not path.exists():
        logger.error(f"Missing required JSON artifact: {path}")
        raise HTTPException(
            status_code=500,
            detail=f"Required artifact is missing.",
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        logger.error(f"Could not load JSON artifact {path.name}: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not load required data artifact.",
        ) from error


def read_csv_artifact(path: Path) -> pd.DataFrame:
    """Load a CSV file and raise a clean HTTP 500 if it is missing or corrupt."""
    if not path.exists():
        logger.error(f"Missing required CSV artifact: {path}")
        raise HTTPException(
            status_code=500,
            detail=f"Required artifact is missing.",
        )
    try:
        return pd.read_csv(path)
    except (OSError, ValueError) as error:
        logger.error(f"Could not load CSV artifact {path.name}: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not load required data artifact.",
        ) from error


def _check_columns(data: pd.DataFrame, required: list[str], artifact_name: str) -> None:
    """Raise HTTP 500 with a clear message if any required columns are absent."""
    missing = [col for col in required if col not in data.columns]
    if missing:
        logger.error(f"{artifact_name} missing columns: {missing}")
        raise HTTPException(
            status_code=500,
            detail=f"Data artifact is missing required columns.",
        )


# ─── Endpoints ────────────────────────────────────────────────────────────────

REQUIRED_READINESS_ARTIFACTS = [
    PROJECT_ROOT / "models" / "linear_regression.joblib",
    PROJECT_ROOT / "models" / "random_forest.joblib",
    PROJECT_ROOT / "models" / "gradient_boosting.joblib",
    PROJECT_ROOT / "models" / "xgboost.joblib",
    PROJECT_ROOT / "data" / "processed" / "model_data" / "preprocessor.joblib",
    PROJECT_ROOT / "models" / "final_diwali_forecast.json",
]


@app.get("/", include_in_schema=False)
def root():
    """Redirect root endpoint to interactive API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["Health"], summary="Check API liveness health")
def health() -> HealthResponse:
    """Return API health, service name, and version."""
    return HealthResponse(
        status="healthy",
        service="gold-price-intelligence-api",
        version=API_VERSION,
    )


@app.get(
    "/ready",
    response_model=ReadinessResponse,
    tags=["Readiness"],
    summary="Check production service readiness",
)
def ready() -> ReadinessResponse:
    """Verify that all required production artifacts are present and readable."""
    checks = {}
    missing = []
    for artifact in REQUIRED_READINESS_ARTIFACTS:
        name = artifact.name
        if artifact.exists() and artifact.stat().st_size > 0:
            checks[name] = "AVAILABLE"
        else:
            checks[name] = "MISSING"
            missing.append(name)

    if missing:
        logger.warning(f"Readiness check failed. Missing artifacts: {missing}")
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready. Missing required production artifacts: {', '.join(missing)}",
        )

    return ReadinessResponse(status="ready", checks=checks)



@app.get(
    "/api/model-info",
    response_model=ModelInfoResponse,
    tags=["Model"],
    summary="Get trained model metadata and performance metrics",
)
def model_info() -> ModelInfoResponse:
    """Return metadata and validation/test performance for the selected model."""
    metadata = read_json_artifact(MODEL_METADATA_PATH)
    return ModelInfoResponse(
        model=metadata["selected_model"],
        validation={key: metadata[f"validation_{key}"] for key in ("MAE", "RMSE", "MAPE", "R2")},
        test={key: metadata[f"test_{key}"] for key in ("MAE", "RMSE", "MAPE", "R2")},
        training_rows=metadata["training_rows"],
        validation_rows=metadata["validation_rows"],
        test_rows=metadata["test_rows"],
        feature_count=metadata["feature_count"],
    )


@app.get(
    "/api/diwali-prediction",
    response_model=DiwaliPredictionResponse,
    tags=["Forecast"],
    summary="Get the frozen Diwali 2026 gold-price forecast",
)
def diwali_prediction() -> DiwaliPredictionResponse:
    """Return the frozen Diwali reference estimate and surrounding business-day forecasts."""
    fc = read_json_artifact(FINAL_FORECAST_PATH)
    return DiwaliPredictionResponse(
        diwali_date=fc["diwali_date"],
        previous_business_day={
            "date": fc["previous_business_day"],
            "forecast": fc["previous_business_day_forecast"],
        },
        diwali_reference_estimate={
            "date": fc["diwali_date"],
            "forecast": fc["diwali_reference_estimate"],
        },
        next_business_day={
            "date": fc["next_business_day"],
            "forecast": fc["next_business_day_forecast"],
        },
        estimated_range={"lower": fc["lower_estimate"], "upper": fc["upper_estimate"]},
        unit=fc["unit"],
        model=fc["selected_model"],
    )


@app.get(
    "/api/weight-prediction",
    response_model=WeightPredictionResponse,
    tags=["Forecast"],
    summary="Get predicted gold price for a specified weight (1g to 15g)",
)
def weight_prediction(
    weight: float = Query(..., description="Gold weight in grams (1.0 to 15.0)")
) -> WeightPredictionResponse:
    """Return predicted Diwali 2026 Gold 999 price and estimated range for specified weight in grams (1.0 to 15.0)."""
    if weight < 1.0 or weight > 15.0:
        raise HTTPException(
            status_code=400,
            detail="Weight must be between 1.0g and 15.0g.",
        )

    fc = read_json_artifact(FINAL_FORECAST_PATH)
    ref_10g = float(fc["diwali_reference_estimate"])
    lower_10g = float(fc["lower_estimate"])
    upper_10g = float(fc["upper_estimate"])

    price_per_gram = ref_10g / 10.0
    pred_price = round(price_per_gram * weight, 2)
    lower_est = round((lower_10g / 10.0) * weight, 2)
    upper_est = round((upper_10g / 10.0) * weight, 2)

    return WeightPredictionResponse(
        weight_grams=weight,
        price_per_10g=round(ref_10g, 2),
        price_per_gram=round(price_per_gram, 3),
        predicted_price=pred_price,
        lower_estimate=lower_est,
        upper_estimate=upper_est,
        currency="INR",
        unit=fc.get("unit", "Gold 999"),
        reference_date=fc["diwali_date"],
        model=fc["selected_model"],
    )


@app.get(
    "/api/forecast",
    response_model=list[ForecastPoint],
    tags=["Forecast"],
    summary="Get the full chronological recursive forecast series",
)
def forecast() -> list[ForecastPoint]:
    """Return all business-day recursive forecast rows, sorted by date ascending."""
    data = read_csv_artifact(FORECAST_PATH)
    required = list(ForecastPoint.model_fields)
    _check_columns(data, required, "Forecast artifact")
    data = data.sort_values("date").reset_index(drop=True)
    return [ForecastPoint(**row) for row in data[required].to_dict(orient="records")]


@app.get(
    "/api/historical-data",
    response_model=list[HistoricalPoint],
    tags=["Historical Data"],
    summary="Get historical IBJA Gold 999 observations",
)
def historical_data() -> list[HistoricalPoint]:
    """Return the full historical IBJA observation series, sorted by date ascending.

    The source CSV uses ``gold_999_average`` as the column name; this endpoint
    normalises it to ``gold_999_avg`` for the frontend.
    """
    data = read_csv_artifact(HISTORICAL_PATH)

    # Normalise column name: gold_999_average → gold_999_avg
    if "gold_999_avg" not in data.columns and "gold_999_average" in data.columns:
        data = data.rename(columns={"gold_999_average": "gold_999_avg"})
    elif "gold_999_avg" not in data.columns:
        raise HTTPException(
            status_code=500,
            detail="Historical artifact is missing the gold_999_avg (or gold_999_average) column.",
        )

    # Replace pandas NaN with None so Pydantic serialises as JSON null
    data = data.where(pd.notna(data), other=None)

    required = list(HistoricalPoint.model_fields)
    _check_columns(data, required, "Historical data artifact")
    data = data.sort_values("date").reset_index(drop=True)
    return [HistoricalPoint(**row) for row in data[required].to_dict(orient="records")]


@app.get(
    "/api/model-comparison",
    response_model=list[ModelComparisonPoint],
    tags=["Model"],
    summary="Compare all evaluated models on the validation set",
)
def model_comparison() -> list[ModelComparisonPoint]:
    """Return validation metrics for all four models, ranked by RMSE → MAE → MAPE → R²."""
    data = read_csv_artifact(VALIDATION_RESULTS_PATH)

    required = ["model", "MAE", "RMSE", "MAPE", "R2"]
    _check_columns(data, required, "Validation results artifact")

    # Coerce numeric columns and validate
    for col in required[1:]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    if data[required[1:]].isna().any().any():
        raise HTTPException(
            status_code=500,
            detail="Validation results contain missing or non-numeric metrics.",
        )

    # Normalise model name labels to canonical long-form names
    data["model"] = data["model"].replace({
        "Random Forest":    "Random Forest Regressor",
        "Gradient Boosting": "Gradient Boosting Regressor",
        "XGBRegressor":     "XGBoost Regressor",
        "XGBoost":          "XGBoost Regressor",
    })

    # Rank: lowest RMSE first, then MAE, then MAPE, then highest R² as tie-break
    data = data.sort_values(
        ["RMSE", "MAE", "MAPE", "R2"],
        ascending=[True, True, True, False],
    ).reset_index(drop=True)

    selected_model = "Linear Regression"
    return [
        ModelComparisonPoint(
            **{col: row[col] for col in required},
            selected=(row["model"] == selected_model),
        )
        for _, row in data.iterrows()
    ]


@app.get(
    "/api/prediction-drivers",
    response_model=PredictionDriversResponse,
    tags=["Explainability"],
    summary="Get Linear Regression feature contributions for Diwali 2026 forecast",
)
def prediction_drivers() -> PredictionDriversResponse:
    """Return feature contributions explaining the Diwali 2026 forecast."""
    data = read_json_artifact(PREDICTION_DRIVERS_PATH)
    return PredictionDriversResponse(**data)


@app.get(
    "/api/what-if",
    response_model=WhatIfResponse,
    tags=["What-If Analysis"],
    summary="Get Diwali 2026 forecast sensitivity analysis under market scenarios",
)
def what_if() -> WhatIfResponse:
    """Return What-If market scenarios from the sensitivity analysis artifact."""
    df = read_csv_artifact(SENSITIVITY_PATH)
    required = ["scenario", "gold_market_adjustment", "usdinr_adjustment", "diwali_reference_estimate"]
    _check_columns(df, required, "Sensitivity analysis artifact")

    display_names = {
        "baseline forecast": "Baseline Model Forecast",
        "international gold forecast +5%": "International Gold +5%",
        "international gold forecast -5%": "International Gold −5%",
        "USD/INR forecast +2%": "USD/INR +2%",
        "USD/INR forecast -2%": "USD/INR −2%",
    }

    market_assumptions = {
        "baseline forecast": "Baseline recursive forecast (Unadjusted market inputs)",
        "international gold forecast +5%": "5% increase in projected international gold prices (USD/oz)",
        "international gold forecast -5%": "5% decrease in projected international gold prices (USD/oz)",
        "USD/INR forecast +2%": "2% appreciation in projected USD/INR exchange rate",
        "USD/INR forecast -2%": "2% depreciation in projected USD/INR exchange rate",
    }

    baseline_row = df[
        df["scenario"].str.lower().str.contains("baseline") |
        ((df["gold_market_adjustment"] == 0.0) & (df["usdinr_adjustment"] == 0.0))
    ]
    if baseline_row.empty:
        baseline_pred = float(df.iloc[0]["diwali_reference_estimate"])
    else:
        baseline_pred = float(baseline_row.iloc[0]["diwali_reference_estimate"])

    scenario_items: list[WhatIfScenario] = []
    for _, row in df.iterrows():
        raw_scen = str(row["scenario"]).strip()
        gold_adj = float(row["gold_market_adjustment"])
        fx_adj = float(row["usdinr_adjustment"])
        pred = float(row["diwali_reference_estimate"])
        change = pred - baseline_pred
        change_pct = (change / baseline_pred) * 100.0 if baseline_pred != 0 else 0.0
        is_base = raw_scen.lower().startswith("baseline") or (gold_adj == 0.0 and fx_adj == 0.0)

        disp_name = display_names.get(raw_scen, raw_scen)
        assumption = market_assumptions.get(
            raw_scen, f"Gold adjustment: {gold_adj:+.1%}, USD/INR adjustment: {fx_adj:+.1%}"
        )

        scenario_items.append(
            WhatIfScenario(
                scenario=raw_scen,
                display_name=disp_name,
                gold_market_adjustment=gold_adj,
                usdinr_adjustment=fx_adj,
                prediction=pred,
                change=change,
                change_percentage=change_pct,
                market_assumption=assumption,
                is_baseline=is_base,
            )
        )

    return WhatIfResponse(baseline_prediction=baseline_pred, scenarios=scenario_items)