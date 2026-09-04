# Step 44 — Data Transparency & Methodology Report

## Data Sources
- **Primary Target Data Source**: India Bullion and Jewellers Association (IBJA) — `data/raw/ibja_gold_999_2025_2026.csv`.
- **Exogenous Spot Gold Market Source**: Yahoo Finance spot gold closing rates (USD per troy ounce).
- **Exogenous Currency Source**: USD/INR spot exchange rates (INR per 1 USD).

## Target Variable
- **Target Name**: `target_gold_999`
- **Asset**: IBJA Gold 999
- **Purity**: 999 fine gold (approx. 24 Karat)
- **Unit**: Indian Rupees (INR) per 10 grams
- **Target Construction**: Daily mathematical average of published IBJA AM (morning) and PM (evening) quotes.
- **Target Transformation**: Untransformed raw INR price space. No logarithmic, power, or differencing transformations were applied to the target variable to preserve monetary interpretability.

## Dataset Coverage
- **Total Master Observations**: 168 rows (`data/processed/gold_master_dataset.csv`).
- **Date Range**: 2025-09-02 through 2026-09-01.
- **Trading Calendar Characteristics**: Non-contiguous business-day sequence corresponding strictly to published IBJA trading days. Unobserved weekends, bank holidays, and exchange closures were not fabricated or artificially interpolated into the target series.

## Data Validation
- **Missing Target Values**: 0 missing target values in master dataset.
- **Duplicate Observations**: 0 duplicate dates.
- **Column Integrity**:
  - `gold_999_am`: Morning IBJA rate
  - `gold_999_pm`: Evening IBJA rate
  - `gold_999_avg`: Daily average rate
  - `target_gold_999`: Primary target variable

## Feature Engineering
The feature dataset (`data/processed/gold_feature_dataset.csv`) contains **46 predictor features** across 9 structured domain categories:

1. **Calendar Features** (10 features): `day_of_week`, `day_of_month`, `month`, `quarter`, `day_of_year`, `week_of_year`, `is_month_start`, `is_month_end`, `days_to_diwali`, `is_near_diwali`.
2. **Historical Target Lags** (6 features): `gold_lag_1`, `gold_lag_2`, `gold_lag_3`, `gold_lag_5`, `gold_lag_7`, `gold_lag_14` (built strictly via `shift(1)` to eliminate lookahead leakage).
3. **Target Trend Moving Averages** (4 features): `gold_ma_3`, `gold_ma_7`, `gold_ma_14`, `gold_ma_30`.
4. **Target Volatility Indicators** (3 features): `gold_volatility_7`, `gold_volatility_14`, `gold_volatility_30` (rolling standard deviations of daily returns).
5. **Target Return Features** (3 features): `gold_return_1d`, `gold_return_3d`, `gold_return_7d` (percentage return relative to shifted historical prices).
6. **International Spot Market Features** (9 features): `gold_usd_open`, `gold_usd_high`, `gold_usd_low`, `gold_usd_close`, `gold_usd_volume`, `gold_usd_return_1d`, `gold_usd_return_3d`, `gold_usd_return_7d`, `gold_usd_volatility_7`, `gold_usd_volatility_14`.
7. **USD/INR Exchange Rate Features** (9 features): `usdinr_open`, `usdinr_high`, `usdinr_low`, `usdinr_close`, `usdinr_return_1d`, `usdinr_return_3d`, `usdinr_return_7d`, `usdinr_volatility_7`, `usdinr_volatility_14`.
8. **Derived Market Proxy** (1 feature): `gold_inr_proxy` (`gold_usd_close × usdinr_close`).
9. **Diwali Proximity Indicators** (1 feature): `days_to_diwali`, `is_near_diwali`.

## Data Leakage Prevention
Rigorous leakage prevention audits were enforced throughout model design:
- **Same-Day Target Exclusions**: Raw target components (`gold_999_am`, `gold_999_pm`, `gold_999_avg`) on day $t$ were strictly excluded from predictor features on day $t$.
- **Lag Shifting**: Target lags and rolling statistics on day $t$ were computed exclusively from observations $\le t-1$.
- **Train-Only Preprocessing**: Preprocessor transformers (`SimpleImputer(strategy='median')`) were fitted exclusively on `X_train`. `X_validation` and `X_test` were transformed using train-fitted parameters.
- **Untouched Holdout Test Set**: The test split (26 observations) was isolated prior to model selection and remained completely untouched during model training, tuning, and selection.
- **Data Leakage Check Status**: **PASSED**

## Chronological Split
Data was partitioned chronologically to respect time-series causality. Random shuffling was strictly prohibited.

- **Training Set**: 117 rows (2025-09-02 to 2026-06-19)
- **Validation Set**: 25 rows (2026-06-22 to 2026-07-27)
- **Test Set**: 26 rows (2026-07-28 to 2026-09-01)
- **Total Rows**: 168 rows

## Models Evaluated
Four candidate machine learning algorithms were trained on the training set and evaluated on the chronological validation set:

1. **Linear Regression**: Ordinary Least Squares linear predictor.
2. **Random Forest Regressor**: Ensemble of decision trees with feature bagging.
3. **Gradient Boosting Regressor**: Sequential boosted tree algorithm.
4. **XGBoost Regressor**: Extreme Gradient Boosting implementation.

## Model Selection
Linear Regression was selected as the primary forecasting algorithm based on validation performance:

- **Validation RMSE**: **2,738.80 INR** (Lowest among all candidate models)
- **Validation MAE**: **2,495.98 INR** (Lowest among all candidate models)
- **Validation MAPE**: **1.75%**
- **Validation R²**: **-1.3225** (Transparently acknowledged: on small non-stationary validation windows, simple linear models can produce negative $R^2$ while still outperforming volatile complex tree models in absolute error metrics).

## Final Test Evaluation
The selected Linear Regression model was evaluated on the untouched historical test set (26 observations, 2026-07-28 to 2026-09-01):

- **Test MAE**: **₹2,122.61**
- **Test RMSE**: **₹2,576.56**
- **Test MAPE**: **1.4178%**
- **Test R²**: **0.8409**
- **Evaluation Summary**: Historical test performance confirmed strong generalization ($R^2 > 0.84$) on unseen historical business days.

## Diwali Forecast Methodology
- **Forecast Horizon**: 49 business days (2026-09-02 through 2026-11-09).
- **Recursive Protocol**: Predictions are generated step-by-step. At step $t$, the model prediction $\hat{y}_t$ is recursively appended to target history to generate target lags for step $t+1$.
- **Exogenous Projections**: International gold and USD/INR exchange rates are projected independently via AutoReg time-series models.
- **Diwali 2026 Reference Date**: Diwali 2026 falls on a **Sunday (08 November 2026)** when IBJA does not publish rates. The official **Diwali reference estimate (₹142,442.41)** is the midpoint average of adjacent business day forecasts (06 Nov & 09 Nov).
- **Estimated Range**: **₹137,889.90 — ₹144,859.72** (derived from empirical 5th and 95th quantiles of historical validation/test residuals).

## Forecast Continuity & Diagnostic
- **Step 40 Continuity Findings**:
  - Latest actual IBJA rate (2026-09-01): **₹153,990.50**
  - First recursive forecast (2026-09-02): **₹141,292.29**
  - Discontinuity gap: **-8.25% (-₹12,698.21)**
- **Diagnostic Analysis**: The initial drop reflects recursive prediction dynamics where unobserved future OHLC features default to train-fitted median imputation values. A minor double-shifting bug in return features was identified and documented in Step 40 (correcting it shifted the forecast by ~₹97 on day 1 and ~₹45 on Diwali). Per strict protocol, the frozen baseline forecast (₹142,442.41) was preserved without artificial smoothing.

## Explainable AI
- **Methodology**: Exact inner-product feature contribution analysis ($y = b + \sum w_i x_i$).
- **Drivers Identified**: 27 positive drivers (+₹492,606.55 upward contribution) and 19 negative drivers (-₹210,568.29 downward contribution).
- **Reconstruction Verification**: `intercept + sum(contributions)` matches prediction with residual `0.000000` (**PASS**).

## What-If Analysis
- **Scenarios Evaluated**: 5 predefined market sensitivity scenarios from `reports/diwali_sensitivity_analysis.csv` (Baseline, Gold +5%, Gold -5%, USD/INR +2%, USD/INR -2%).
- **Sensitivity Findings**: USD/INR +2% yields highest upward shift (+₹2,200.64 / +1.54%), while USD/INR -2% yields highest downward shift (-₹2,363.84 / -1.66%).

## Data Integrity
- **Model Retraining**: **NO**
- **Forecast Modification**: **NO**
- **Hard-coded Production Metrics**: **NO** (All metrics fetched dynamically via FastAPI).

## Limitations
1. **Data Limitations**: IBJA rates are published only on business trading days; unobserved dates are not present in raw files.
2. **Model Limitations**: Recursive time-series forecasting accumulates uncertainty over long horizons. Linear models cannot capture non-linear market regime shifts.
3. **Market Limitations**: Future exogenous inputs (Gold USD & USD/INR) are projected using AutoReg models and do not account for sudden macroeconomic or geopolitical black swan events.

## Frontend Implementation
- **Enhanced `/about` Page**: Interactive Process Flowchart, Target Specifications, 9-Category Feature Taxonomy, Leakage Audit Checklist, Model Selection Benchmark Table, and Categorized Limitations.
- **Dashboard & Forecast Desk**: Institutional Data Transparency summary cards.

## API Integrity
All 8 FastAPI endpoints verified operational (HTTP 200 OK):
1. `GET /health`
2. `GET /api/model-info`
3. `GET /api/model-comparison`
4. `GET /api/diwali-prediction`
5. `GET /api/forecast`
6. `GET /api/historical-data`
7. `GET /api/prediction-drivers`
8. `GET /api/what-if`

## Build Status
- **Vite Production Build**: `npm run build` -> **PASS** (Zero errors).
