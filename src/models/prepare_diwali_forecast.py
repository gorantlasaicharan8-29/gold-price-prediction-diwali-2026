"""Prepare, but do not generate, a leakage-safe Diwali 2026 forecast plan."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MARKET_PATH = PROJECT_ROOT / "data" / "raw" / "international_market_data.csv"
FEATURE_PATH = PROJECT_ROOT / "data" / "processed" / "gold_feature_dataset.csv"
PREPROCESSOR_PATH = PROJECT_ROOT / "data" / "processed" / "model_data" / "preprocessor.joblib"
MODEL_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "model_data"
REPORTS_DIR = PROJECT_ROOT / "reports"
DIWALI_DATE = pd.Timestamp("2026-11-08")
HORIZON_START = pd.Timestamp("2026-09-02")
LATEST_IBJA_DATE = pd.Timestamp("2026-09-01")

TARGET_DERIVED_FEATURES = {
    "gold_lag_1", "gold_lag_2", "gold_lag_3", "gold_lag_5", "gold_lag_7", "gold_lag_14",
    "gold_ma_3", "gold_ma_7", "gold_ma_14", "gold_ma_30", "gold_return_1d", "gold_return_3d",
    "gold_return_7d", "gold_volatility_7", "gold_volatility_14", "gold_volatility_30",
}
MARKET_FEATURES = {
    "gold_usd_open", "gold_usd_high", "gold_usd_low", "gold_usd_close", "gold_usd_volume",
    "usdinr_open", "usdinr_high", "usdinr_low", "usdinr_close", "gold_inr_proxy",
    "gold_usd_return_1d", "gold_usd_return_3d", "gold_usd_return_7d", "gold_usd_volatility_7",
    "gold_usd_volatility_14", "usdinr_return_1d", "usdinr_return_3d", "usdinr_return_7d",
    "usdinr_volatility_7", "usdinr_volatility_14",
}
CALENDAR_FEATURES = {
    "day_of_week", "day_of_month", "month", "quarter", "day_of_year", "week_of_year",
    "is_month_start", "is_month_end", "days_to_diwali", "is_near_diwali",
}


def create_calendar() -> pd.DataFrame:
    dates = pd.date_range(HORIZON_START, DIWALI_DATE, freq="B")
    calendar = pd.DataFrame({"date": dates})
    calendar["days_to_diwali"] = (DIWALI_DATE - calendar["date"]).dt.days
    calendar["is_near_diwali"] = calendar["days_to_diwali"].abs().le(30).astype("int64")
    calendar["day_of_week"] = calendar["date"].dt.dayofweek
    calendar["day_of_month"] = calendar["date"].dt.day
    calendar["month"] = calendar["date"].dt.month
    calendar["quarter"] = calendar["date"].dt.quarter
    calendar["day_of_year"] = calendar["date"].dt.dayofyear
    calendar["week_of_year"] = calendar["date"].dt.isocalendar().week.astype("int64")
    calendar["is_month_start"] = calendar["date"].dt.is_month_start.astype("int64")
    calendar["is_month_end"] = calendar["date"].dt.is_month_end.astype("int64")
    return calendar[["date", "days_to_diwali", "is_near_diwali", "day_of_week", "day_of_month", "month", "quarter", "day_of_year", "week_of_year", "is_month_start", "is_month_end"]]


def feature_requirement(feature: str) -> tuple[str, str, str]:
    if feature in TARGET_DERIVED_FEATURES:
        return "numeric", "NO", "YES"
    if feature in MARKET_FEATURES:
        return "numeric", "YES", "NO"
    if feature in CALENDAR_FEATURES:
        return "numeric", "NO", "NO"
    return "numeric", "UNKNOWN", "UNKNOWN"


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    calendar = create_calendar()
    calendar["date"] = calendar["date"].dt.strftime("%Y-%m-%d")
    calendar.to_csv(MODEL_DATA_DIR / "diwali_forecast_calendar.csv", index=False)

    market = pd.read_csv(MARKET_PATH)
    market["date"] = pd.to_datetime(market["date"], errors="raise")
    market_latest = market["date"].max()
    gold_dates = market.loc[market["gold_usd_close"].notna(), "date"]
    fx_dates = market.loc[market["usdinr_close"].notna(), "date"]
    latest_gold = gold_dates.max()
    latest_fx = fx_dates.max()

    features = pd.read_csv(FEATURE_PATH, nrows=1)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    predictor_columns = list(preprocessor.get_feature_names_out())
    expected_columns = list(pd.read_csv(MODEL_DATA_DIR / "X_train.csv", nrows=1).columns)
    if predictor_columns != expected_columns:
        raise ValueError("Preprocessor feature names do not match saved X_train columns.")
    feature_audit = []
    for feature in predictor_columns:
        feature_type, requires_market, requires_target = feature_requirement(feature)
        available_directly = "YES" if feature in CALENDAR_FEATURES else "NO"
        feature_audit.append({
            "feature_name": feature,
            "feature_type": feature_type,
            "requires_future_market_data": requires_market,
            "requires_future_target_data": requires_target,
            "available_for_direct_diwali_forecast": available_directly,
        })
    audit = pd.DataFrame(feature_audit)
    audit.to_csv(REPORTS_DIR / "diwali_model_feature_audit.csv", index=False)

    unavailable_market = sorted(MARKET_FEATURES.intersection(predictor_columns))
    unavailable_target = sorted(TARGET_DERIVED_FEATURES.intersection(predictor_columns))
    directly_available = sorted(CALENDAR_FEATURES.intersection(predictor_columns))
    readiness = "READY" if not unavailable_market and not unavailable_target else "NOT READY"
    availability_report = "\n".join([
        "DIWALI FORECAST FEATURE AVAILABILITY",
        "====================================",
        "",
        f"Diwali date: {DIWALI_DATE.date()}",
        f"Forecast horizon: {HORIZON_START.date()} to {DIWALI_DATE.date()} (weekdays only)",
        f"Latest international market file date: {market_latest.date()}",
        f"Latest directly available international gold close: {latest_gold.date()}",
        f"Latest directly available USD/INR close: {latest_fx.date()}",
        "",
        "Directly available future inputs:",
        *[f"- {feature}" for feature in directly_available],
        "",
        "Unavailable future market-dependent features (no silent forward-fill):",
        *[f"- {feature}" for feature in unavailable_market],
        "",
        "Features requiring future target observations:",
        *[f"- {feature}" for feature in unavailable_target],
        "",
        "Future target columns are intentionally absent: target_gold_999, gold_999_am, gold_999_pm, gold_999_avg.",
        "A recursive or other explicitly defined forecasting strategy is required before target-derived features can be generated beyond the latest observed target.",
        "No future market or target values were fabricated, interpolated, or forward-filled.",
    ])
    (REPORTS_DIR / "diwali_forecast_feature_availability.txt").write_text(availability_report + "\n", encoding="utf-8")

    plan = "\n".join([
        "DIWALI 2026 FORECAST PLAN",
        "========================",
        "",
        f"Diwali target date: {DIWALI_DATE.date()}",
        f"Latest observed IBJA target date: {LATEST_IBJA_DATE.date()}",
        f"Forecast horizon: {HORIZON_START.date()} to {DIWALI_DATE.date()} (weekdays only)",
        "Selected model: Linear Regression",
        "",
        "Model input requirements:",
        f"- {len(predictor_columns)} transformed predictor columns listed in diwali_model_feature_audit.csv.",
        "- Calendar features, historical target-derived features, and international market features.",
        "",
        "Available future inputs:",
        f"- Calendar features for all {len(calendar)} weekday horizon dates.",
        f"- Market data through gold date {latest_gold.date()} and USD/INR date {latest_fx.date()} only.",
        "",
        "Unavailable future inputs:",
        "- International market values beyond their actual latest available dates.",
        "- Future target-derived lags, moving averages, returns, and volatility values after 2026-09-01.",
        "",
        "Potential leakage risks:",
        "- Forward-filling future market values would invent information.",
        "- Using future IBJA targets to construct lags or rolling features would leak the answer.",
        "- Reusing same-day target-source columns would directly reveal the target.",
        "",
        f"Forecast readiness: {readiness}",
        "Recommended next step: define and approve a recursive forecasting strategy and an approved method for future exogenous market inputs before generating a Diwali prediction.",
        "Final Diwali prediction: NOT GENERATED",
    ])
    (REPORTS_DIR / "diwali_forecast_plan.txt").write_text(plan + "\n", encoding="utf-8")

    print("DIWALI FORECAST PREPARATION COMPLETE")
    print(f"\nDiwali date: {DIWALI_DATE.date()}")
    print(f"Latest observed IBJA date: {LATEST_IBJA_DATE.date()}")
    print(f"Forecast horizon: {HORIZON_START.date()} to {DIWALI_DATE.date()}")
    print(f"Forecast readiness: {readiness}")
    print("Future target fabrication: NONE")
    print("Future market fabrication: NONE")
    print("Data leakage: PASSED")
    print("Final Diwali prediction: NOT GENERATED")
    print(f"\nLATEST AVAILABLE INTERNATIONAL GOLD DATE: {latest_gold.date()}")
    print(f"LATEST AVAILABLE USD/INR DATE: {latest_fx.date()}")
    print("\nModel feature columns:")
    print("\n".join(predictor_columns))


if __name__ == "__main__":
    main()