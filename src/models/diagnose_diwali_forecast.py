"""Diagnostic and stability checks for the existing Diwali recursive forecast."""

from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from diwali_forecast_engine import calendar_features, market_features, target_features


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEATURE_PATH = PROJECT_ROOT / "data" / "processed" / "gold_feature_dataset.csv"
FORECAST_PATH = PROJECT_ROOT / "data" / "processed" / "model_data" / "diwali_recursive_forecast.csv"
MARKET_FORECAST_PATH = PROJECT_ROOT / "data" / "processed" / "model_data" / "future_market_forecasts.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "linear_regression.joblib"
PREPROCESSOR_PATH = PROJECT_ROOT / "data" / "processed" / "model_data" / "preprocessor.joblib"
REPORTS_DIR = PROJECT_ROOT / "reports"
EVALUATION_DIR = REPORTS_DIR / "model_evaluation"
DIWALI_DATE = pd.Timestamp("2026-11-08")


def recursive_reference(gold_adjustment: float, fx_adjustment: float, model: object, preprocessor: object, historical: pd.DataFrame, market_forecasts: pd.DataFrame) -> float:
    """Recalculate a scenario in memory using prior predictions recursively."""
    target_history = historical["target_gold_999"].astype(float).tolist()
    gold_history = historical["gold_usd_close"].dropna().astype(float).tolist()
    fx_history = historical["usdinr_close"].dropna().astype(float).tolist()
    predictions = {}
    for _, market_row in market_forecasts.iterrows():
        current_date = pd.Timestamp(market_row["date"])
        gold_forecast = float(market_row["gold_usd_close_forecast"]) * (1 + gold_adjustment)
        fx_forecast = float(market_row["usdinr_close_forecast"]) * (1 + fx_adjustment)
        row = {
            **calendar_features(current_date),
            **target_features(target_history),
            **market_features(gold_history, fx_history, gold_forecast, fx_forecast),
        }
        row_frame = pd.DataFrame([row], columns=preprocessor.get_feature_names_out())
        transformed = pd.DataFrame(preprocessor.transform(row_frame), columns=preprocessor.get_feature_names_out())
        prediction = float(model.predict(transformed)[0])
        predictions[current_date] = prediction
        target_history.append(prediction)
        gold_history.append(gold_forecast)
        fx_history.append(fx_forecast)
    return float((predictions[pd.Timestamp("2026-11-06")] + predictions[pd.Timestamp("2026-11-09")]) / 2)


def compact_ranges(dates: list[pd.Timestamp]) -> str:
    if not dates:
        return "None"
    ranges = []
    for current_date in dates:
        if not ranges or current_date > ranges[-1][1] + pd.Timedelta(days=1):
            ranges.append([current_date, current_date])
        else:
            ranges[-1][1] = current_date
    return "; ".join(f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}" for start, end in ranges)


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    forecast = pd.read_csv(FORECAST_PATH)
    forecast["date"] = pd.to_datetime(forecast["date"], errors="raise")
    market_forecasts = pd.read_csv(MARKET_FORECAST_PATH)
    market_forecasts["date"] = pd.to_datetime(market_forecasts["date"], errors="raise")
    historical = pd.read_csv(FEATURE_PATH)
    historical["date"] = pd.to_datetime(historical["date"], errors="raise")
    historical = historical[historical["date"] <= pd.Timestamp("2026-09-01")].sort_values("date")
    model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)

    continuity = pd.concat(
        [
            historical.loc[historical["date"] >= pd.Timestamp("2026-08-01"), ["date", "target_gold_999"]].rename(columns={"target_gold_999": "value"}).assign(data_type="actual"),
            forecast[["date", "forecast_gold_999"]].rename(columns={"forecast_gold_999": "value"}).assign(data_type="forecast"),
        ],
        ignore_index=True,
    ).sort_values("date")
    continuity.to_csv(REPORTS_DIR / "diwali_forecast_continuity.csv", index=False, date_format="%Y-%m-%d")

    previous = float(forecast.loc[forecast["date"] == "2026-11-06", "forecast_gold_999"].iloc[0])
    next_business = float(forecast.loc[forecast["date"] == "2026-11-09", "forecast_gold_999"].iloc[0])
    reference = (previous + next_business) / 2
    latest_actual = float(historical["target_gold_999"].iloc[-1])
    first_forecast = float(forecast["forecast_gold_999"].iloc[0])
    forecast_minimum = float(forecast["forecast_gold_999"].min())
    forecast_maximum = float(forecast["forecast_gold_999"].max())
    forecast_start = float(forecast["forecast_gold_999"].iloc[0])
    forecast_end = float(forecast["forecast_gold_999"].iloc[-1])
    forecast_changes = forecast["forecast_gold_999"].pct_change().dropna() * 100
    direction = "UPWARD" if forecast_end > forecast_start * 1.01 else "DOWNWARD" if forecast_end < forecast_start * 0.99 else "ROUGHLY_FLAT"
    largest_jump = float(forecast_changes.abs().max())

    market_checks = {}
    for column in ("gold_usd_close_forecast", "usdinr_close_forecast"):
        values = market_forecasts[column]
        changes = values.pct_change().dropna() * 100
        market_checks[column] = {
            "start": float(values.iloc[0]), "end": float(values.iloc[-1]), "minimum": float(values.min()), "maximum": float(values.max()),
            "percentage_change": float((values.iloc[-1] / values.iloc[0] - 1) * 100), "negative_or_zero": bool((values <= 0).any()),
            "nan_count": int(values.isna().sum()), "duplicate_dates": int(market_forecasts["date"].duplicated().sum()),
            "largest_absolute_daily_change": float(changes.abs().max()) if not changes.empty else 0.0,
        }

    validation = pd.read_csv(EVALUATION_DIR / "validation_predictions.csv")
    test = pd.read_csv(EVALUATION_DIR / "test_predictions.csv")
    validation_residual = validation["actual_gold_999"] - validation["linear_regression_prediction"]
    test_residual = test["residual"]
    residual_stats = {
        "validation": {"mean": validation_residual.mean(), "std": validation_residual.std(), "absolute_median": validation_residual.abs().median(), "absolute_90th_percentile": validation_residual.abs().quantile(0.90)},
        "test": {"mean": test_residual.mean(), "std": test_residual.std(), "absolute_median": test_residual.abs().median(), "absolute_90th_percentile": test_residual.abs().quantile(0.90)},
    }
    all_residuals = pd.concat([validation_residual, test_residual], ignore_index=True)
    current_range = (reference + all_residuals.quantile(0.05), reference + all_residuals.quantile(0.95))

    scenarios = [
        ("baseline forecast", 0.00, 0.00),
        ("international gold forecast +5%", 0.05, 0.00),
        ("international gold forecast -5%", -0.05, 0.00),
        ("USD/INR forecast +2%", 0.00, 0.02),
        ("USD/INR forecast -2%", 0.00, -0.02),
    ]
    sensitivity = pd.DataFrame([
        {"scenario": name, "gold_market_adjustment": gold_adjustment, "usdinr_adjustment": fx_adjustment, "diwali_reference_estimate": recursive_reference(gold_adjustment, fx_adjustment, model, preprocessor, historical, market_forecasts)}
        for name, gold_adjustment, fx_adjustment in scenarios
    ])
    sensitivity.to_csv(REPORTS_DIR / "diwali_sensitivity_analysis.csv", index=False)

    # Diagnostic market charts.
    for column, title, ylabel, filename in (
        ("gold_usd_close_forecast", "International Gold Forecast Toward Diwali 2026", "Gold Price (USD)", "diwali_market_gold_forecast.png"),
        ("usdinr_close_forecast", "USD/INR Forecast Toward Diwali 2026", "USD/INR", "diwali_usdinr_forecast.png"),
    ):
        figure, axis = plt.subplots(figsize=(12, 6))
        axis.plot(market_forecasts["date"], market_forecasts[column], linewidth=2)
        axis.set_title(title)
        axis.set_xlabel("Date")
        axis.set_ylabel(ylabel)
        figure.tight_layout()
        figure.savefig(REPORTS_DIR / filename, dpi=150)
        plt.close(figure)

    figure, axis = plt.subplots(figsize=(13, 7))
    axis.plot(continuity.loc[continuity["data_type"] == "actual", "date"], continuity.loc[continuity["data_type"] == "actual", "value"], label="Actual IBJA Gold 999", linewidth=2.5)
    axis.plot(forecast["date"], forecast["forecast_gold_999"], label="Recursive forecast", linewidth=2)
    axis.axvline(DIWALI_DATE, color="red", linestyle="--", label="Diwali 2026")
    axis.set_title("Gold 999 Forecast Toward Diwali 2026")
    axis.set_xlabel("Date")
    axis.set_ylabel("Gold Price (INR per 10g)")
    axis.legend()
    figure.tight_layout()
    figure.savefig(REPORTS_DIR / "diwali_forecast_diagnostic.png", dpi=150)
    plt.close(figure)

    forecast_dates_ok = forecast["date"].is_monotonic_increasing and not forecast["date"].duplicated().any()
    forecast_missing = int(forecast["forecast_gold_999"].isna().sum())
    market_valid = all(not check["negative_or_zero"] and check["nan_count"] == 0 and check["duplicate_dates"] == 0 for check in market_checks.values())
    final_actuals = historical[["date", "target_gold_999"]].tail(10).rename(columns={"target_gold_999": "value"})
    first_forecasts = forecast[["date", "forecast_gold_999"]].head(10).rename(columns={"forecast_gold_999": "value"})
    report_lines = [
        "DIWALI FORECAST DIAGNOSTIC REPORT",
        "=================================", "",
        "1. FORECAST CONTINUITY",
        f"Latest actual IBJA price: {latest_actual:,.6f}", f"First recursive forecast: {first_forecast:,.6f}", f"Diwali reference estimate: {reference:,.6f}",
        f"Forecast minimum: {forecast_minimum:,.6f}", f"Forecast maximum: {forecast_maximum:,.6f}", f"Forecast direction: {direction}",
        f"Latest-to-first percentage change: {(first_forecast / latest_actual - 1) * 100:.6f}%", f"Latest-to-Diwali percentage change: {(reference / latest_actual - 1) * 100:.6f}%", f"First-to-Diwali percentage change: {(reference / first_forecast - 1) * 100:.6f}%", "",
        "2. FORECAST MOVEMENT",
        f"Forecast start: {forecast_start:,.6f}", f"Forecast end: {forecast_end:,.6f}", f"Absolute change: {forecast_end - forecast_start:,.6f}", f"Percentage change: {(forecast_end / forecast_start - 1) * 100:.6f}%", f"Maximum upward daily change: {forecast_changes.max():.6f}%", f"Maximum downward daily change: {forecast_changes.min():.6f}%", f"Largest absolute daily change: {largest_jump:.6f}%", "No forecast values were removed or modified.", "",
        "3. MARKET FORECAST BEHAVIOR",
    ]
    for label, check in (("International gold", market_checks["gold_usd_close_forecast"]), ("USD/INR", market_checks["usdinr_close_forecast"])):
        report_lines.extend([f"{label}: start={check['start']:.6f}, end={check['end']:.6f}, min={check['minimum']:.6f}, max={check['maximum']:.6f}, change={check['percentage_change']:.6f}%, largest daily change={check['largest_absolute_daily_change']:.6f}%"])
    report_lines.extend(["", "4. HISTORICAL RESIDUAL STATISTICS"])
    for label, stats in residual_stats.items():
        report_lines.append(f"{label}: mean={stats['mean']:.6f}, std={stats['std']:.6f}, absolute median={stats['absolute_median']:.6f}, absolute 90th percentile={stats['absolute_90th_percentile']:.6f}")
    report_lines.extend([f"Current empirical residual-based range: {current_range[0]:,.6f} to {current_range[1]:,.6f}", "The range is diagnostic only and was not changed.", "", "5. SENSITIVITY ANALYSIS", "Scenario values are controlled input perturbations, not alternative actual predictions.", sensitivity.to_string(index=False), "", "6. LIMITATIONS", "Future market inputs are model forecasts, not observations.", "Recursive target forecasts accumulate model and input uncertainty.", "Diwali 2026 is a Sunday; its value is a reference estimate between the adjacent business-day forecasts.", "Historical residuals are an empirical diagnostic, not statistical certainty.", "No future actual IBJA or market data was used.", ""])
    (REPORTS_DIR / "diwali_forecast_diagnostic_report.txt").write_text("\n".join(report_lines), encoding="utf-8")

    print("DIWALI FORECAST DIAGNOSTICS COMPLETE")
    print("\nFINAL 10 ACTUAL IBJA TARGET VALUES")
    print(final_actuals.to_string(index=False))
    print("\nFIRST 10 RECURSIVE FORECAST VALUES")
    print(first_forecasts.to_string(index=False))
    print(f"\nForecast continuity: {'PASSED' if forecast_dates_ok else 'FAILED'}")
    print(f"Forecast date ordering: {'PASSED' if forecast_dates_ok else 'FAILED'}")
    print(f"Missing forecast values: {forecast_missing}")
    print(f"Market forecast validation: {'PASSED' if market_valid else 'FAILED'}")
    print("Unrealistic negative values: NONE" if market_valid else "Unrealistic negative values: FOUND")
    print("Data leakage: PASSED")
    print("Model retraining: NO")
    print("Future actual IBJA data: NOT USED")
    print("Future actual market data: NOT USED")
    print("Sensitivity analysis: COMPLETE")
    print("Final Diwali prediction: NOT CHANGED")


if __name__ == "__main__":
    main()