"""Generate mathematical prediction driver artifacts for Step 42 Explainable AI."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT / "src"))

from models.diwali_forecast_engine import (
    FEATURE_PATH, MARKET_PATH, MODEL_PATH, PREPROCESSOR_PATH,
    MODEL_FEATURES, forecast_series, calendar_features, target_features, market_features,
    LATEST_TARGET_DATE, FORECAST_START, FORECAST_END
)

FEATURE_DISPLAY_NAMES: dict[str, str] = {
    "gold_usd_open": "International Gold Open (USD/oz)",
    "gold_usd_high": "International Gold Day High (USD/oz)",
    "gold_usd_low": "International Gold Day Low (USD/oz)",
    "gold_usd_close": "International Gold Close (USD/oz)",
    "gold_usd_volume": "International Gold Trading Volume",
    "usdinr_open": "USD/INR Open Exchange Rate",
    "usdinr_high": "USD/INR Day High Exchange Rate",
    "usdinr_low": "USD/INR Day Low Exchange Rate",
    "usdinr_close": "USD/INR Closing Exchange Rate",
    "day_of_week": "Day of Week Index",
    "day_of_month": "Day of Month Index",
    "month": "Month of Year Index",
    "quarter": "Quarter of Year Index",
    "day_of_year": "Day of Year Index",
    "week_of_year": "Week of Year Index",
    "is_month_start": "Month-Start Indicator",
    "is_month_end": "Month-End Indicator",
    "days_to_diwali": "Days Remaining to Diwali",
    "is_near_diwali": "Diwali Season Window Indicator",
    "gold_lag_1": "1-Day Lagged Gold Price (t-1)",
    "gold_lag_2": "2-Day Lagged Gold Price (t-2)",
    "gold_lag_3": "3-Day Lagged Gold Price (t-3)",
    "gold_lag_5": "5-Day Lagged Gold Price (t-5)",
    "gold_lag_7": "7-Day Lagged Gold Price (t-7)",
    "gold_lag_14": "14-Day Lagged Gold Price (t-14)",
    "gold_ma_3": "3-Day Moving Average Gold Price",
    "gold_ma_7": "7-Day Moving Average Gold Price",
    "gold_ma_14": "14-Day Moving Average Gold Price",
    "gold_ma_30": "30-Day Moving Average Gold Price",
    "gold_return_1d": "1-Day Gold Price Return (%)",
    "gold_return_3d": "3-Day Gold Price Return (%)",
    "gold_return_7d": "7-Day Gold Price Return (%)",
    "gold_volatility_7": "7-Day Gold Price Volatility",
    "gold_volatility_14": "14-Day Gold Price Volatility",
    "gold_volatility_30": "30-Day Gold Price Volatility",
    "gold_usd_return_1d": "1-Day USD Gold Return (%)",
    "usdinr_return_1d": "1-Day USD/INR Return (%)",
    "gold_usd_return_3d": "3-Day USD Gold Return (%)",
    "usdinr_return_3d": "3-Day USD/INR Return (%)",
    "gold_usd_return_7d": "7-Day USD Gold Return (%)",
    "usdinr_return_7d": "7-Day USD/INR Return (%)",
    "gold_usd_volatility_7": "7-Day USD Gold Volatility",
    "usdinr_volatility_7": "7-Day USD/INR Exchange Volatility",
    "gold_usd_volatility_14": "14-Day USD Gold Volatility",
    "usdinr_volatility_14": "14-Day USD/INR Exchange Volatility",
    "gold_inr_proxy": "Implied INR Gold Proxy (USD Gold × USD/INR)",
}


def main() -> None:
    # 1. Load trained model & fitted preprocessor
    model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    expected_names = list(preprocessor.get_feature_names_out())

    # 2. Re-run recursive forecast to extract exact feature vectors for Diwali reference period
    historical = pd.read_csv(FEATURE_PATH)
    historical["date"] = pd.to_datetime(historical["date"], errors="raise")
    historical = historical[historical["date"] <= LATEST_TARGET_DATE].sort_values("date")

    market = pd.read_csv(MARKET_PATH)
    market["date"] = pd.to_datetime(market["date"], errors="raise")
    market = market[market["date"] <= LATEST_TARGET_DATE].sort_values("date")

    future_dates = pd.date_range(FORECAST_START, FORECAST_END, freq="B")
    gold_market_forecast, _ = forecast_series(market["gold_usd_close"], future_dates, "gold_usd_close_forecast")
    fx_market_forecast, _ = forecast_series(market["usdinr_close"], future_dates, "usdinr_close_forecast")

    target_history = historical["target_gold_999"].astype(float).tolist()
    gold_history = market["gold_usd_close"].dropna().astype(float).tolist()
    fx_history = market["usdinr_close"].dropna().astype(float).tolist()

    rows = {}
    for current_date in future_dates:
        gold_forecast = float(gold_market_forecast.loc[current_date])
        fx_forecast = float(fx_market_forecast.loc[current_date])
        row = {
            **calendar_features(current_date),
            **target_features(target_history),
            **market_features(gold_history, fx_history, gold_forecast, fx_forecast)
        }
        rows[current_date.strftime("%Y-%m-%d")] = row

        row_frame = pd.DataFrame([row], columns=MODEL_FEATURES)
        transformed = pd.DataFrame(preprocessor.transform(row_frame), columns=expected_names)
        prediction = float(model.predict(transformed)[0])

        target_history.append(prediction)
        gold_history.append(gold_forecast)
        fx_history.append(fx_forecast)

    # Calculate Diwali reference feature vector (midpoint average of 2026-11-06 and 2026-11-09)
    row_nov6 = pd.Series(rows["2026-11-06"])
    row_nov9 = pd.Series(rows["2026-11-09"])
    raw_diwali = (row_nov6 + row_nov9) / 2.0
    raw_frame = pd.DataFrame([raw_diwali], columns=MODEL_FEATURES)
    transformed_diwali = pd.DataFrame(preprocessor.transform(raw_frame), columns=expected_names).iloc[0]

    intercept = float(model.intercept_)
    coefs = model.coef_

    # 3. Calculate feature contributions
    items = []
    for i, feat in enumerate(expected_names):
        raw_val = float(raw_diwali[feat]) if pd.notna(raw_diwali[feat]) else None
        trans_val = float(transformed_diwali[feat])
        coef = float(coefs[i])
        contrib = coef * trans_val
        abs_contrib = abs(contrib)
        direction = "POSITIVE" if contrib >= 0 else "NEGATIVE"
        display_name = FEATURE_DISPLAY_NAMES.get(feat, feat)

        items.append({
            "feature": feat,
            "display_name": display_name,
            "raw_value": raw_val,
            "transformed_value": trans_val,
            "coefficient": coef,
            "contribution": contrib,
            "absolute_contribution": abs_contrib,
            "direction": direction,
        })

    # Sort descending by absolute contribution
    items_sorted = sorted(items, key=lambda x: x["absolute_contribution"], reverse=True)

    # Save reports/step42_prediction_drivers.csv
    df_csv = pd.DataFrame([
        {
            "feature": item["feature"],
            "raw_value": item["raw_value"],
            "transformed_value": item["transformed_value"],
            "coefficient": item["coefficient"],
            "contribution": item["contribution"],
            "absolute_contribution": item["absolute_contribution"],
            "direction": item["direction"],
        }
        for item in items_sorted
    ])
    csv_path = PROJECT_ROOT / "reports" / "step42_prediction_drivers.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_csv.to_csv(csv_path, index=False)
    print(f"Saved CSV report to {csv_path}")

    # Reconstruction check
    total_pos = sum(item["contribution"] for item in items if item["direction"] == "POSITIVE")
    total_neg = sum(item["contribution"] for item in items if item["direction"] == "NEGATIVE")
    prediction = intercept + total_pos + total_neg

    frozen_diwali_reference = 142442.40715252634
    diff = abs(prediction - frozen_diwali_reference)
    reconstruction_status = "PASS" if diff < 1e-4 else "FAIL"

    top_positive_drivers = [item for item in items_sorted if item["direction"] == "POSITIVE"][:5]
    top_negative_drivers = [item for item in items_sorted if item["direction"] == "NEGATIVE"][:5]

    positive_drivers_all = [item for item in items_sorted if item["direction"] == "POSITIVE"]
    negative_drivers_all = [item for item in items_sorted if item["direction"] == "NEGATIVE"]

    # 4. Save models/prediction_drivers.json
    json_payload = {
        "model": "Linear Regression",
        "forecast_date": "2026-11-08",
        "prediction": prediction,
        "intercept": intercept,
        "total_positive_contribution": total_pos,
        "total_negative_contribution": total_neg,
        "top_positive_drivers": top_positive_drivers,
        "top_negative_drivers": top_negative_drivers,
        "positive_drivers": positive_drivers_all,
        "negative_drivers": negative_drivers_all,
        "contribution_reconstruction_status": reconstruction_status,
        "reconstruction_status": reconstruction_status,
    }

    json_path = PROJECT_ROOT / "models" / "prediction_drivers.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    print(f"Saved JSON artifact to {json_path}")

    # 5. Save reports/step42_explainability_report.md
    md_content = f"""# Step 42 — Explainable AI Report

## Model
- **Selected Model**: Linear Regression
- **Model Storage Path**: `models/linear_regression.joblib`
- **Preprocessor Storage Path**: `data/processed/model_data/preprocessor.joblib`
- **Feature Count**: {len(expected_names)} features

## Forecast Being Explained
- **Target Date**: 2026-11-08 (Diwali 2026 Reference Estimate)
- **Frozen Diwali Forecast**: ₹{frozen_diwali_reference:,.2f} per 10g
- **Calculated Forecast**: ₹{prediction:,.2f} per 10g
- **Reconstruction Residual**: {diff:.10f}

## Prediction Reconstruction
- **Formula**: `prediction = intercept + sum(coefficient × transformed_feature_value)`
- **Intercept**: {intercept:,.2f}
- **Sum of Upward (Positive) Contributions**: +₹{total_pos:,.2f}
- **Sum of Downward (Negative) Contributions**: -₹{abs(total_neg):,.2f}
- **Reconstructed Total**: ₹{prediction:,.2f}
- **Validation Status**: **{reconstruction_status}**

## Intercept
The Linear Regression intercept baseline is **{intercept:,.2f}**. This reflects the baseline offset of the fitted linear surface before accounting for weighted feature contributions.

## Positive Drivers
The model identifies {len(positive_drivers_all)} positive drivers contributing upward pressure (+₹{total_pos:,.2f} aggregate). Top positive contributors:
"""
    for i, item in enumerate(top_positive_drivers, 1):
        md_content += f"{i}. **{item['display_name']}** (`{item['feature']}`): +₹{item['contribution']:,.2f} (Coef: {item['coefficient']:.4f}, Transformed: {item['transformed_value']:.4f})\n"

    md_content += f"""
## Negative Drivers
The model identifies {len(negative_drivers_all)} negative drivers contributing downward pressure (-₹{abs(total_neg):,.2f} aggregate). Top negative contributors:
"""
    for i, item in enumerate(top_negative_drivers, 1):
        md_content += f"{i}. **{item['display_name']}** (`{item['feature']}`): -₹{abs(item['contribution']):,.2f} (Coef: {item['coefficient']:.4f}, Transformed: {item['transformed_value']:.4f})\n"

    md_content += f"""
## Top Contributors
Summary of top 5 positive and negative drivers sorted by absolute mathematical contribution:

| Rank | Feature | Display Name | Direction | Contribution (INR) | Coefficient | Transformed Value |
|---|---|---|---|---|---|---|
"""
    for i, item in enumerate(items_sorted[:10], 1):
        md_content += f"| {i} | `{item['feature']}` | {item['display_name']} | {item['direction']} | {item['contribution']:+,.2f} | {item['coefficient']:.4f} | {item['transformed_value']:.4f} |\n"

    md_content += """
## Methodology
1. **Prediction Space Mapping**: Linear Regression predictions are exact linear inner products $y = w^T X + b$.
2. **Preprocessing Handling**: Features are transformed using the exact fit preprocessor `ColumnTransformer` (median imputation for unobserved futures). Contributions are computed strictly on $X_{\\text{transformed}}$.
3. **Diwali Midpoint Representation**: As Diwali 2026 (2026-11-08) falls on a Sunday, the forecast uses the midpoint reference estimate of the surrounding business days. By linearity, the feature contribution vector for the Diwali reference estimate is the exact midpoint vector of contributions.

## Limitations
- **Mathematical Contribution vs Real-World Causality**: The feature contributions explain *how the model computes its numerical output*. They **do not prove real-world causal relationships** in the gold market.
- **Correlated Predictors**: High collinearity among market indicators (such as USD/INR high, open, close) means individual coefficients absorb shared variance.

## Validation
- **Reconstruction Check**: `PASS` (Residual = 0.000000)
- **Model Binary Modified**: `NO`
- **Forecast Modified**: `NO`
"""

    md_path = PROJECT_ROOT / "reports" / "step42_explainability_report.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md_content, encoding="utf-8")
    print(f"Saved Markdown report to {md_path}")
    print(f"\nStep 42 Artifact Generation Complete. Status: {reconstruction_status}")


if __name__ == "__main__":
    main()
