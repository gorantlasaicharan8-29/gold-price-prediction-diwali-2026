# Step 42 — Explainability Implementation Report

## Implementation Summary
A mathematically exact Explainable AI (XAI) capability has been integrated into the Gold Price Prediction System to explain the Linear Regression model forecast for Diwali 2026. The feature contribution analysis operates strictly on the model's inner-product prediction space, preserving full model integrity and frozen forecast values.

## Model Used
- **Selected Model**: Linear Regression (`models/linear_regression.joblib`)
- **Preprocessor**: ColumnTransformer with median imputation (`data/processed/model_data/preprocessor.joblib`)
- **Model Retrained**: **NO**

## Forecast Explained
- **Target Date**: 2026-11-08 (Diwali 2026)
- **Frozen Reference Forecast**: ₹142,442.41 per 10g
- **Estimated Range**: ₹137,889.90 — ₹144,859.72 per 10g
- **Forecast Modified**: **NO**

## Contribution Method
- **Mathematical Space**: $y = b + \sum_{i=1}^{p} w_i x_i^{\text{transformed}}$
- **Feature Vector**: Exact transformed feature vector derived from `preprocessor.transform()`.
- **Contribution Calculation**: $\text{contribution}_i = w_i \times x_i^{\text{transformed}}$
- **Absolute Ranking**: Features are sorted by $|\text{contribution}_i|$ descending.

## Positive Drivers
- **Count**: 27 positive features (+₹492,606.55 aggregate upward contribution)
- **Top 5 Positive Contributors**:
  1. `usdinr_high` (*USD/INR Day High Exchange Rate*): +₹109,408.82
  2. `usdinr_close` (*USD/INR Closing Exchange Rate*): +₹95,437.91
  3. `gold_usd_high` (*International Gold Day High*): +₹94,830.95
  4. `usdinr_open` (*USD/INR Open Exchange Rate*): +₹78,720.08
  5. `gold_usd_low` (*International Gold Day Low*): +₹32,935.98

## Negative Drivers
- **Count**: 19 negative features (-₹210,568.29 aggregate downward contribution)
- **Top 5 Negative Contributors**:
  1. `usdinr_low` (*USD/INR Day Low Exchange Rate*): -₹94,600.18
  2. `gold_usd_close` (*International Gold Close*): -₹59,069.82
  3. `gold_ma_3` (*3-Day Moving Average Gold Price*): -₹17,814.58
  4. `gold_ma_7` (*7-Day Moving Average Gold Price*): -₹15,706.98
  5. `gold_lag_14` (*14-Day Lagged Gold Price*): -₹9,529.14

## Reconstruction Validation
- **Linear Intercept Baseline ($b$)**: -₹139,595.86
- **Total Positive Sum**: +₹492,606.55
- **Total Negative Sum**: -₹210,568.29
- **Reconstructed Forecast**: $b + \sum \text{contrib}_i = ₹142,442.41$
- **Reconstruction Residual**: `0.000000`
- **Reconstruction Status**: **PASS**

## API Integration
- **Endpoint**: `GET /api/prediction-drivers`
- **Implementation**: Dynamic endpoint loading `models/prediction_drivers.json` with Pydantic response validation (`PredictionDriversResponse`).
- **Error Handling**: Graceful HTTP 500 without stack trace leaks.
- **Verification Status**: **PASS** (200 OK)

## Frontend Integration
- **Component**: `frontend/src/components/PredictionDrivers.jsx`
- **Presentation**: Dual-column layout displaying **UPWARD CONTRIBUTORS (+)** and **DOWNWARD CONTRIBUTORS (-)** with relative contribution bars, directional badges, and human-readable feature labels.
- **Toggle View**: User toggle for *Top 5 Contributors* vs *All Feature Drivers (46)*.
- **Hover Tooltips**: Instant detail popovers revealing raw value, transformed value, coefficient ($w_i$), and contribution.
- **Verification Status**: **PASS**

## Accessibility
- **WCAG Compliance**: High-contrast typography, directional indicators (`+` / `−`), semantic heading hierarchy (`h2`, `h3`), `aria-labelledby`, `role="list"`, `role="listitem"`, and keyboard-navigable card focus states (`tabIndex={0}`).

## Responsive Design
- **Breakpoints Validated**: 1440px, 1280px, 768px, 390px.
- **Layout Behavior**: Grid transitions smoothly from 2 columns to 1 stacked column on mobile without horizontal scrolling.

## Build Status
- **Vite Production Build**: `npm run build` -> **PASS** (`dist/` generated cleanly in 935ms).

## Forecast Integrity
- **Model Retrained**: **NO**
- **Forecast Regenerated**: **NO**
- **Frozen Forecast Unchanged**: **YES** (₹142,442.41 reference estimate maintained).

## Limitations
- Mathematical feature contributions explain the internal mechanics of the Linear Regression prediction space ($y = b + \sum w_i x_i$). They indicate feature weights in the trained model, not causal physical mechanisms in the real-world gold market.
