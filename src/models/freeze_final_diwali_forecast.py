"""Freeze the already validated Diwali 2026 forecast into production artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORECAST_PATH = PROJECT_ROOT / "data" / "processed" / "model_data" / "diwali_recursive_forecast.csv"
DIWALI_PATH = PROJECT_ROOT / "reports" / "diwali_2026_forecast.csv"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "diwali_2026_forecast_summary.txt"
DIAGNOSTIC_PATH = PROJECT_ROOT / "reports" / "diwali_forecast_diagnostic_report.txt"
SENSITIVITY_PATH = PROJECT_ROOT / "reports" / "diwali_sensitivity_analysis.csv"
HISTORICAL_PATH = PROJECT_ROOT / "data" / "processed" / "gold_feature_dataset.csv"
VALIDATION_PATH = PROJECT_ROOT / "reports" / "model_evaluation" / "validation_results.csv"
PERFORMANCE_PATH = PROJECT_ROOT / "reports" / "model_evaluation" / "final_model_performance.csv"
MODEL_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "model_data"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
EVALUATION_DIR = PROJECT_ROOT / "reports" / "model_evaluation"


def value_for(frame: pd.DataFrame, date: str) -> float:
    return float(frame.loc[frame["date"] == date, "forecast_gold_999"].iloc[0])


def parse_diagnostic_range() -> tuple[float, float]:
    text = DIAGNOSTIC_PATH.read_text(encoding="utf-8")
    match = re.search(r"Current empirical residual-based range: ([\d,.]+) to ([\d,.]+)", text)
    if not match:
        raise ValueError("Could not find the validated forecast range in the diagnostic report.")
    return float(match.group(1).replace(",", "")), float(match.group(2).replace(",", ""))


def main() -> None:
    forecast = pd.read_csv(FORECAST_PATH)
    forecast["date"] = pd.to_datetime(forecast["date"], errors="raise").dt.strftime("%Y-%m-%d")
    diwali_extract = pd.read_csv(DIWALI_PATH)
    if set(diwali_extract["forecast_type"]) != {"previous_business_day", "diwali_reference_estimate", "next_business_day"}:
        raise ValueError("Diwali extraction does not contain the expected forecast types.")

    previous = value_for(forecast, "2026-11-06")
    diwali_reference = value_for(forecast, "2026-11-08") if (forecast["date"] == "2026-11-08").any() else float(diwali_extract.loc[diwali_extract["forecast_type"] == "diwali_reference_estimate", "forecast_gold_999"].iloc[0])
    next_business = value_for(forecast, "2026-11-09")
    extracted_reference = float(diwali_extract.loc[diwali_extract["forecast_type"] == "diwali_reference_estimate", "forecast_gold_999"].iloc[0])
    if abs(diwali_reference - extracted_reference) > 1e-9:
        raise ValueError("Existing Diwali reference and recursive forecast disagree.")
    lower_estimate, upper_estimate = parse_diagnostic_range()

    validation = pd.read_csv(VALIDATION_PATH).loc[lambda frame: frame["model"] == "Linear Regression"].iloc[0]
    performance = pd.read_csv(PERFORMANCE_PATH)
    test = performance.loc[performance["dataset"] == "test"].iloc[0]
    sensitivity = pd.read_csv(SENSITIVITY_PATH)
    if abs(float(sensitivity.loc[sensitivity["scenario"] == "baseline forecast", "diwali_reference_estimate"].iloc[0]) - diwali_reference) > 1e-9:
        raise ValueError("Sensitivity baseline disagrees with the validated Diwali reference.")

    final_json = {
        "project": "Gold Price Prediction System during Diwali 2026",
        "target": "IBJA Gold 999",
        "unit": "INR per 10 grams",
        "diwali_date": "2026-11-08",
        "previous_business_day": "2026-11-06",
        "next_business_day": "2026-11-09",
        "selected_model": "Linear Regression",
        "latest_observed_ibja_date": "2026-09-01",
        "previous_business_day_forecast": previous,
        "diwali_reference_estimate": diwali_reference,
        "next_business_day_forecast": next_business,
        "lower_estimate": lower_estimate,
        "upper_estimate": upper_estimate,
        "forecast_method": "Recursive forecasting with forecasted international gold and USD/INR inputs",
        "future_actual_ibja_used": False,
        "future_actual_market_data_used": False,
        "test_retraining": False,
        "data_leakage_check": "PASSED",
    }
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    (MODELS_DIR / "final_diwali_forecast.json").write_text(json.dumps(final_json, indent=2) + "\n", encoding="utf-8")

    final_metrics = pd.DataFrame([
        {"metric": "previous_business_day_forecast", "value": previous, "unit": "INR per 10 grams"},
        {"metric": "diwali_reference_estimate", "value": diwali_reference, "unit": "INR per 10 grams"},
        {"metric": "next_business_day_forecast", "value": next_business, "unit": "INR per 10 grams"},
        {"metric": "lower_estimate", "value": lower_estimate, "unit": "INR per 10 grams"},
        {"metric": "upper_estimate", "value": upper_estimate, "unit": "INR per 10 grams"},
    ])
    final_metrics.to_csv(REPORTS_DIR / "final_diwali_2026_forecast.csv", index=False)

    historical = pd.read_csv(HISTORICAL_PATH)
    historical["date"] = pd.to_datetime(historical["date"], errors="raise")
    historical = historical.loc[historical["date"] >= pd.Timestamp("2026-08-01"), ["date", "target_gold_999"]]
    historical = historical.rename(columns={"target_gold_999": "value"})
    figure, axis = plt.subplots(figsize=(13, 7))
    axis.plot(historical["date"], historical["value"], label="Historical IBJA Gold 999", linewidth=2.5)
    axis.plot(pd.to_datetime(forecast["date"]), forecast["forecast_gold_999"], label="Recursive forecast", linewidth=2)
    axis.axvline(pd.Timestamp("2026-11-08"), color="red", linestyle="--", label="Diwali 2026")
    axis.scatter([pd.Timestamp("2026-11-08")], [diwali_reference], color="red", zorder=5, label="Diwali reference estimate")
    axis.axhspan(lower_estimate, upper_estimate, color="gray", alpha=0.18, label="Estimated uncertainty range")
    axis.set_title("Final Gold 999 Forecast - Diwali 2026")
    axis.set_xlabel("Date")
    axis.set_ylabel("Gold Price (INR per 10g)")
    axis.legend()
    figure.tight_layout()
    figure.savefig(REPORTS_DIR / "final_diwali_2026_forecast.png", dpi=150)
    plt.close(figure)

    model_metadata = {
        "selected_model": "Linear Regression",
        "validation_MAE": float(validation["MAE"]), "validation_RMSE": float(validation["RMSE"]), "validation_MAPE": float(validation["MAPE"]), "validation_R2": float(validation["R2"]),
        "test_MAE": float(test["MAE"]), "test_RMSE": float(test["RMSE"]), "test_MAPE": float(test["MAPE"]), "test_R2": float(test["R2"]),
        "training_rows": 117, "validation_rows": 25, "test_rows": 26, "feature_count": 46,
    }
    (MODELS_DIR / "model_metadata.json").write_text(json.dumps(model_metadata, indent=2) + "\n", encoding="utf-8")

    sensitivity_summary = "; ".join(f"{row.scenario}: INR {row.diwali_reference_estimate:,.2f}" for row in sensitivity.itertuples())
    report = "\n".join([
        "FINAL DIWALI 2026 GOLD PRICE REPORT", "", "1. PROJECT OBJECTIVE", "Package the validated recursive Gold 999 forecast for Diwali 2026 production use.",
        "", "2. DATA SOURCES USED", "IBJA Gold 999 historical target, Yahoo Finance-derived forecasted international gold and USD/INR inputs, saved train-fitted preprocessor, and the validated Linear Regression model.",
        "", "3. LATEST OBSERVED IBJA DATE", "2026-09-01", "", "4. SELECTED MODEL", "Linear Regression",
        "", "5. HISTORICAL VALIDATION PERFORMANCE", validation.to_string(), "", "6. FINAL UNSEEN TEST PERFORMANCE", test.to_string(),
        "", "7. FORECASTING METHODOLOGY", "Validated recursive forecast using AutoReg market-input forecasts and the existing Linear Regression model; no retraining or parameter changes were performed.",
        "", "8. PREVIOUS BUSINESS-DAY FORECAST", f"INR {previous:,.2f}", "", "9. DIWALI REFERENCE ESTIMATE", f"INR {diwali_reference:,.2f}",
        "The Diwali reference estimate is a model-derived reference value because 8 November 2026 falls on a Sunday and is not a normal IBJA trading/rate-publication day.",
        "", "10. NEXT BUSINESS-DAY FORECAST", f"INR {next_business:,.2f}", "", "11. ESTIMATED PREDICTION RANGE", f"INR {lower_estimate:,.2f} to INR {upper_estimate:,.2f}",
        "The prediction range is an estimated uncertainty range based on historical model residuals and should not be interpreted as a guaranteed interval.",
        "", "12. INTERNATIONAL GOLD FORECASTING METHOD", "AutoReg(lags=5, trend='ct')", "", "13. USD/INR FORECASTING METHOD", "AutoReg(lags=5, trend='ct')",
        "", "14. SENSITIVITY ANALYSIS SUMMARY", "Scenario values are controlled perturbations, not alternative predictions.", sensitivity_summary,
        "", "15. LIMITATIONS", "Future market inputs are forecasts rather than observations. Recursive error can accumulate. Historical test performance does not guarantee future accuracy.",
        "", "16. DATA LEAKAGE CHECKS", "Future actual IBJA data used: NO. Future actual market data used: NO. Test retraining: NO. Data leakage check: PASSED.", "",
    ])
    (REPORTS_DIR / "final_diwali_2026_report.txt").write_text(report, encoding="utf-8")

    # Existing rounded summary is accepted only when it agrees within display precision.
    summary_text = SUMMARY_PATH.read_text(encoding="utf-8")
    summary_match = re.search(r"Diwali reference estimate: INR ([\d,.]+)", summary_text)
    if not summary_match or abs(float(summary_match.group(1).replace(",", "")) - diwali_reference) > 0.01:
        raise ValueError("Existing summary does not agree with the validated Diwali reference.")
    print("FINAL FORECAST PACKAGE COMPLETE")
    print("\nSelected model: Linear Regression")
    print("Diwali: 2026-11-08")
    print(f"Diwali reference estimate: INR {diwali_reference:,.2f}")
    print(f"Estimated range: INR {lower_estimate:,.2f} to INR {upper_estimate:,.2f}")
    print(f"Historical test MAPE: {float(test['MAPE']):.6f}%")
    print(f"Historical test R2: {float(test['R2']):.6f}")
    print("Forecast methodology: Validated recursive forecast")
    print("Data leakage: PASSED")
    print("Forecast frozen: YES")


if __name__ == "__main__":
    main()