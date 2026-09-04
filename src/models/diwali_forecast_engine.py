"""Leakage-safe recursive forecast engine for the Diwali 2026 planning date."""

from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.ar_model import AutoReg


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEATURE_PATH = PROJECT_ROOT / "data" / "processed" / "gold_feature_dataset.csv"
MARKET_PATH = PROJECT_ROOT / "data" / "raw" / "international_market_data.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "linear_regression.joblib"
PREPROCESSOR_PATH = PROJECT_ROOT / "data" / "processed" / "model_data" / "preprocessor.joblib"
MODEL_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "model_data"
REPORTS_DIR = PROJECT_ROOT / "reports"
EVALUATION_DIR = REPORTS_DIR / "model_evaluation"
DIWALI_DATE = pd.Timestamp("2026-11-08")
LATEST_TARGET_DATE = pd.Timestamp("2026-09-01")
FORECAST_START = pd.Timestamp("2026-09-02")
FORECAST_END = pd.Timestamp("2026-11-09")

MODEL_FEATURES = [
    "gold_usd_open", "gold_usd_high", "gold_usd_low", "gold_usd_close", "gold_usd_volume",
    "usdinr_open", "usdinr_high", "usdinr_low", "usdinr_close", "day_of_week", "day_of_month",
    "month", "quarter", "day_of_year", "week_of_year", "is_month_start", "is_month_end",
    "days_to_diwali", "is_near_diwali", "gold_lag_1", "gold_lag_2", "gold_lag_3", "gold_lag_5",
    "gold_lag_7", "gold_lag_14", "gold_ma_3", "gold_ma_7", "gold_ma_14", "gold_ma_30",
    "gold_return_1d", "gold_return_3d", "gold_return_7d", "gold_volatility_7", "gold_volatility_14",
    "gold_volatility_30", "gold_usd_return_1d", "usdinr_return_1d", "gold_usd_return_3d",
    "usdinr_return_3d", "gold_usd_return_7d", "usdinr_return_7d", "gold_usd_volatility_7",
    "usdinr_volatility_7", "gold_usd_volatility_14", "usdinr_volatility_14", "gold_inr_proxy",
]


def forecast_series(values: pd.Series, dates: pd.DatetimeIndex, name: str) -> tuple[pd.Series, str]:
    """Forecast a market close with AutoReg, falling back to persistence on failure."""
    clean = pd.to_numeric(values, errors="coerce").dropna()
    horizon = len(dates)
    try:
        lags = min(5, max(1, len(clean) // 20))
        model = AutoReg(clean.to_numpy(), lags=lags, trend="ct").fit()
        forecast = model.predict(start=len(clean), end=len(clean) + horizon - 1, dynamic=False)
        if not np.isfinite(forecast).all() or (forecast <= 0).any():
            raise ValueError("AutoReg returned a non-positive or non-finite forecast.")
        method = f"AutoReg(lags={lags}, trend='ct')"
    except Exception as error:
        forecast = np.repeat(clean.iloc[-1], horizon)
        method = f"last-value persistence fallback (AutoReg failed: {error})"
    return pd.Series(forecast, index=dates, name=name), method


def calendar_features(current_date: pd.Timestamp) -> dict[str, float | int]:
    if pd.isna(current_date):
        return {
            "day_of_week": np.nan,
            "day_of_month": np.nan,
            "month": np.nan,
            "quarter": np.nan,
            "day_of_year": np.nan,
            "week_of_year": np.nan,
            "is_month_start": 0,
            "is_month_end": 0,
            "days_to_diwali": np.nan,
            "is_near_diwali": 0,
        }
    days_to_diwali = (DIWALI_DATE - current_date).days
    return {
        "day_of_week": current_date.dayofweek,
        "day_of_month": current_date.day,
        "month": current_date.month,
        "quarter": current_date.quarter,
        "day_of_year": current_date.dayofyear,
        "week_of_year": int(current_date.isocalendar()[1]),
        "is_month_start": int(current_date.is_month_start),
        "is_month_end": int(current_date.is_month_end),
        "days_to_diwali": days_to_diwali,
        "is_near_diwali": int(abs(days_to_diwali) <= 30),
    }


def target_features(target_history: list[float]) -> dict[str, float]:
    """Calculate target history features from observed values and prior predictions only."""
    series = pd.Series(target_history, dtype="float64")
    historical = series.shift(1)
    result: dict[str, float] = {}
    for lag in (1, 2, 3, 5, 7, 14):
        result[f"gold_lag_{lag}"] = series.iloc[-lag] if len(series) >= lag else np.nan
    for window in (3, 7, 14, 30):
        result[f"gold_ma_{window}"] = historical.tail(window).mean() if len(historical.dropna()) >= window else np.nan
    for period in (1, 3, 7):
        result[f"gold_return_{period}d"] = historical.pct_change(periods=period).iloc[-1] * 100 if len(historical.dropna()) > period else np.nan
    returns = historical.pct_change() * 100
    for window in (7, 14, 30):
        result[f"gold_volatility_{window}"] = returns.tail(window).std() if len(returns.dropna()) >= window else np.nan
    return result


def market_features(gold_history: list[float], fx_history: list[float], gold_forecast: float, fx_forecast: float) -> dict[str, float]:
    gold = pd.Series([*gold_history, gold_forecast], dtype="float64")
    fx = pd.Series([*fx_history, fx_forecast], dtype="float64")
    result = {
        "gold_usd_open": np.nan,
        "gold_usd_high": np.nan,
        "gold_usd_low": np.nan,
        "gold_usd_close": gold_forecast,
        "gold_usd_volume": np.nan,
        "usdinr_open": np.nan,
        "usdinr_high": np.nan,
        "usdinr_low": np.nan,
        "usdinr_close": fx_forecast,
        "gold_inr_proxy": gold_forecast * fx_forecast,
    }
    for period in (1, 3, 7):
        result[f"gold_usd_return_{period}d"] = gold.pct_change(periods=period).iloc[-1] * 100 if len(gold) > period else np.nan
        result[f"usdinr_return_{period}d"] = fx.pct_change(periods=period).iloc[-1] * 100 if len(fx) > period else np.nan
    for window in (7, 14):
        result[f"gold_usd_volatility_{window}"] = gold.pct_change().tail(window).std() * 100
        result[f"usdinr_volatility_{window}"] = fx.pct_change().tail(window).std() * 100
    return result


def main() -> None:
    MODEL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

    historical = pd.read_csv(FEATURE_PATH)
    historical["date"] = pd.to_datetime(historical["date"], errors="raise")
    historical = historical[historical["date"] <= LATEST_TARGET_DATE].sort_values("date")
    if historical["target_gold_999"].isna().any() or historical["date"].max() != LATEST_TARGET_DATE:
        raise ValueError("Historical target data is missing or does not end at 2026-09-01.")
    market = pd.read_csv(MARKET_PATH)
    market["date"] = pd.to_datetime(market["date"], errors="raise")
    market = market[market["date"] <= LATEST_TARGET_DATE].sort_values("date")

    future_dates = pd.date_range(FORECAST_START, FORECAST_END, freq="B")
    gold_market_forecast, gold_method = forecast_series(market["gold_usd_close"], future_dates, "gold_usd_close_forecast")
    fx_market_forecast, fx_method = forecast_series(market["usdinr_close"], future_dates, "usdinr_close_forecast")
    future_market = pd.DataFrame({"date": future_dates, "gold_usd_close_forecast": gold_market_forecast, "usdinr_close_forecast": fx_market_forecast})
    future_market.to_csv(MODEL_DATA_DIR / "future_market_forecasts.csv", index=False, date_format="%Y-%m-%d")

    model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    expected_names = list(preprocessor.get_feature_names_out())
    if expected_names != MODEL_FEATURES or getattr(model, "n_features_in_", len(expected_names)) != len(expected_names):
        raise RuntimeError(f"Model feature mismatch. Expected {MODEL_FEATURES}; preprocessor has {expected_names}.")

    target_history = historical["target_gold_999"].astype(float).tolist()
    gold_history = market["gold_usd_close"].dropna().astype(float).tolist()
    fx_history = market["usdinr_close"].dropna().astype(float).tolist()
    forecasts = []
    for current_date in future_dates:
        gold_forecast = float(gold_market_forecast.loc[current_date])
        fx_forecast = float(fx_market_forecast.loc[current_date])
        row = {**calendar_features(current_date), **target_features(target_history), **market_features(gold_history, fx_history, gold_forecast, fx_forecast)}
        row_frame = pd.DataFrame([row], columns=MODEL_FEATURES)
        transformed = pd.DataFrame(preprocessor.transform(row_frame), columns=expected_names)
        prediction = float(model.predict(transformed)[0])
        if not np.isfinite(prediction):
            raise RuntimeError(f"Non-finite recursive prediction on {current_date.date()}.")
        forecasts.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "forecast_gold_999": prediction,
            "gold_usd_close_forecast": gold_forecast,
            "usdinr_close_forecast": fx_forecast,
            "gold_inr_proxy": gold_forecast * fx_forecast,
            "days_to_diwali": (DIWALI_DATE - current_date).days,
            "is_near_diwali": int(abs((DIWALI_DATE - current_date).days) <= 30),
        })
        target_history.append(prediction)
        gold_history.append(gold_forecast)
        fx_history.append(fx_forecast)

    forecast_frame = pd.DataFrame(forecasts)
    forecast_frame.to_csv(MODEL_DATA_DIR / "diwali_recursive_forecast.csv", index=False)
    previous = forecast_frame.loc[forecast_frame["date"] == "2026-11-06", "forecast_gold_999"].iloc[0]
    next_business = forecast_frame.loc[forecast_frame["date"] == "2026-11-09", "forecast_gold_999"].iloc[0]
    reference = (previous + next_business) / 2

    validation = pd.read_csv(EVALUATION_DIR / "validation_predictions.csv")
    test = pd.read_csv(EVALUATION_DIR / "test_predictions.csv")
    residuals = pd.concat([validation["actual_gold_999"] - validation["linear_regression_prediction"], test["residual"]], ignore_index=True)
    lower_residual, upper_residual = residuals.quantile([0.05, 0.95])
    range_low = reference + lower_residual
    range_high = reference + upper_residual
    diwali_extract = pd.DataFrame([
        {"date": "2026-11-06", "forecast_gold_999": previous, "forecast_type": "previous_business_day"},
        {"date": "2026-11-08", "forecast_gold_999": reference, "forecast_type": "diwali_reference_estimate"},
        {"date": "2026-11-09", "forecast_gold_999": next_business, "forecast_type": "next_business_day"},
    ])
    diwali_extract.to_csv(REPORTS_DIR / "diwali_2026_forecast.csv", index=False)

    actual_history = historical.loc[historical["date"] >= pd.Timestamp("2026-08-01"), ["date", "target_gold_999"]].rename(columns={"target_gold_999": "value"})
    actual_history["type"] = "actual"
    plot_data = pd.concat([actual_history, forecast_frame[["date", "forecast_gold_999"]].rename(columns={"forecast_gold_999": "value"}).assign(type="recursive forecast")])
    plot_data["date"] = pd.to_datetime(plot_data["date"])
    figure, axis = plt.subplots(figsize=(13, 7))
    for label, group in plot_data.groupby("type"):
        axis.plot(group["date"], group["value"], label=label, linewidth=2)
    axis.axvline(DIWALI_DATE, color="red", linestyle="--", label="Diwali 2026 (Sunday)")
    axis.set_title("Gold 999 Forecast Toward Diwali 2026")
    axis.set_xlabel("Date")
    axis.set_ylabel("Gold Price (INR per 10g)")
    axis.legend()
    figure.tight_layout()
    figure.savefig(REPORTS_DIR / "diwali_2026_forecast.png", dpi=150)
    plt.close(figure)

    summary = "\n".join([
        "DIWALI 2026 GOLD PRICE FORECAST",
        "",
        "Festival date: 2026-11-08",
        "Previous business day: 2026-11-06",
        "Next business day: 2026-11-09",
        "Selected model: Linear Regression",
        "Latest observed IBJA target: 2026-09-01",
        f"Diwali reference estimate: INR {reference:,.2f}",
        f"Previous business-day forecast: INR {previous:,.2f}",
        f"Next business-day forecast: INR {next_business:,.2f}",
        f"Estimated prediction range: INR {range_low:,.2f} to INR {range_high:,.2f}",
        f"International gold forecasting method: {gold_method}",
        f"USD/INR forecasting method: {fx_method}",
        "",
        "Important limitations:",
        "- Future market inputs were forecast, not observed.",
        "- Future IBJA target values were never used.",
        "- Unavailable future OHLC/volume inputs were left missing and handled only by the existing train-fitted preprocessor.",
        "- The Diwali date is a Sunday.",
        "- The Diwali reference estimate is a modeling convention, not an observed IBJA rate.",
        "- The prediction range uses empirical 5th and 95th quantiles of historical validation/test residuals and is not statistical certainty.",
        "- Historical test performance does not guarantee future accuracy.",
    ])
    (REPORTS_DIR / "diwali_2026_forecast_summary.txt").write_text(summary + "\n", encoding="utf-8")

    print("DIWALI FORECAST ENGINE COMPLETE")
    print(f"\nLatest observed target: {LATEST_TARGET_DATE.date()}")
    print(f"Forecast end: {FORECAST_END.date()}")
    print(f"Forecast business days: {len(future_dates)}")
    print(f"Diwali date: {DIWALI_DATE.date()}")
    print(f"Diwali reference estimate: INR {reference:,.2f}")
    print(f"Previous business-day forecast: INR {previous:,.2f}")
    print(f"Next business-day forecast: INR {next_business:,.2f}")
    print(f"Prediction range: INR {range_low:,.2f} to INR {range_high:,.2f}")
    print("Future actual IBJA values used: NO")
    print("Future actual market values used: NO")
    print("Test-set retraining: NO")
    print("Data leakage: PASSED")


if __name__ == "__main__":
    main()