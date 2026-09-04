# Step 43 — What-If Analysis Report

## Objective
The objective of Step 43 is to provide an interactive **What-If Scenario Analysis** capability in the application using **ONLY** the authoritative sensitivity analysis results in `reports/diwali_sensitivity_analysis.csv`. This enables users to explore how the model-derived Diwali 2026 reference estimate changes under predefined market shifts, while maintaining strict protection over frozen forecasts and model artifacts.

## Existing Sensitivity Data
- **Authoritative File Source**: `reports/diwali_sensitivity_analysis.csv`
- **Total Predefined Scenarios**: 5 scenarios (including baseline)
- **Data Integrity**: No scenarios were created, modified, or hard-coded. All values are read directly from the CSV artifact.

## Scenario Definitions
The 5 predefined scenarios present in `reports/diwali_sensitivity_analysis.csv` are:

| Scenario Key | Display Name | Gold Market Shift | USD/INR Shift | Model Diwali Estimate (INR/10g) | Variance from Baseline (INR) | Percentage Shift |
|---|---|---|---|---|---|---|
| `baseline forecast` | **Baseline Model Forecast** | 0.0% | 0.0% | **₹142,442.41** | ₹0.00 | 0.00% |
| `international gold forecast +5%` | **International Gold +5%** | +5.0% | 0.0% | **₹141,027.81** | -₹1,414.60 | -0.99% |
| `international gold forecast -5%` | **International Gold −5%** | -5.0% | 0.0% | **₹143,778.68** | +₹1,336.27 | +0.94% |
| `USD/INR forecast +2%` | **USD/INR +2%** | 0.0% | +2.0% | **₹144,643.05** | +₹2,200.64 | +1.54% |
| `USD/INR forecast -2%` | **USD/INR −2%** | 0.0% | -2.0% | **₹140,078.57** | -₹2,363.84 | -1.66% |

## Baseline
- **Baseline Estimate**: **₹142,442.41 per 10g**
- **Forecast Method**: Recursive forecasting with unadjusted AutoReg market projections.
- **Diwali Date**: 2026-11-08 (Sunday reference interpolation).

## Scenario Comparison
- **USD/INR Currency Impact**: A +2% exchange rate shift yields the highest positive impact (+₹2,200.64 / +1.54%), whereas a -2% exchange rate shift yields the highest negative impact (-₹2,363.84 / -1.66%).
- **International Gold Spot Impact**: A -5% drop in international gold forecast increases domestic IBJA estimate (+₹1,336.27 / +0.94%), while a +5% rise decreases it (-₹1,414.60 / -0.99%), reflecting inverse coefficient weighting in the fitted Linear Regression model space.

## API Implementation
- **Endpoint**: `GET /api/what-if`
- **Response Model**: `WhatIfResponse` containing `baseline_prediction` and `scenarios` list (`WhatIfScenario`).
- **Dynamic Data Source**: Reads `reports/diwali_sensitivity_analysis.csv` via `read_csv_artifact()`. No hard-coded prediction values.

## Frontend Implementation
- **Component**: `frontend/src/components/WhatIfAnalysis.jsx`
- **Location**: Mounted on `/forecast` (Forecast Desk) after Prediction Drivers.
- **Visual Presentation**: Includes a baseline spotlight card, predefined scenario grid cards, a horizontal bar comparison chart, and focused detail panels.
- **Mandatory Notice**: *"These scenarios are sensitivity analysis, not additional forecasts."*

## Data Integrity
- **No Hard-coded Scenario Predictions**: All production values consumed dynamically from `/api/what-if`.
- **Model Retraining**: **NO**
- **Forecast Modification**: **NO**

## Responsive Design
- **Breakpoints Validated**: 1440px (desktop), 1280px (laptop), 768px (tablet), 390px (mobile).
- **Behavior**: Horizontal scenario bars collapse cleanly into single-column layout on mobile viewports without horizontal text overflow.

## Accessibility
- **WCAG Compliance**: Clear non-color directional indicators (*Higher than baseline* / *Lower than baseline*), ARIA landmarks (`role="list"`, `role="listitem"`), focusable card elements (`tabIndex={0}`), and high-contrast color scheme.

## Error Handling
- **Missing/Corrupt File Handling**: If `reports/diwali_sensitivity_analysis.csv` is unavailable, API returns HTTP 500 cleanly without stack traces. Frontend displays a user-friendly alert (*"Scenario analysis is currently unavailable."*) with a retry button.

## Build Status
- **Vite Production Build**: `npm run build` -> **PASS** (943ms build time, zero errors).

## Forecast Integrity
- **Frozen Reference Estimate**: ₹142,442.41 per 10g (UNCHANGED)
- **Frozen Forecast Range**: ₹137,889.90 — ₹144,859.72 per 10g (UNCHANGED)
- **Model Binaries**: UNCHANGED

## Limitations
- **Sensitivity Analysis Scope**: Scenarios represent static sensitivity stress-tests on exogenous market inputs. They are **not additional forecasts** or guarantees of future market prices.
- **Predefined Assumptions**: Only the 5 approved scenarios present in `reports/diwali_sensitivity_analysis.csv` are displayed; arbitrary user-entered inputs are intentionally disallowed.
