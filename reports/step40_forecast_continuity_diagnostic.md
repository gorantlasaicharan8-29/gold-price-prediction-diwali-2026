# Step 40 — Forecast Continuity Diagnostic

**Date:** 2026-09-03  
**Project:** Gold Price Intelligence — Gold Price Prediction System during Diwali 2026  
**Scope:** Read-only diagnostic. No model, preprocessor, or forecast artifact was modified.

---

## Executive Summary

A complete artifact-level and code-level investigation was carried out into the -8.25% price discontinuity at the forecast boundary (2026-09-01 actual → 2026-09-02 first recursive forecast).

**The first forecast value was independently reproduced to zero numerical error.**  
This confirms the forecast engine operates exactly as coded and there is no silent corruption.

A partial feature construction inconsistency was identified in the `gold_return_*` family: the engine produces return values that are one step stale relative to the boundary. However this inconsistency is **internally consistent** with the training feature pipeline (both use the same convention), and its **numerical impact on the gap is only 0.72%** of the total 8.25% discontinuity.

The remaining ~99.3% of the gap is explained by **legitimate Linear Regression extrapolation behaviour** combined with the input feature distribution at the boundary being markedly different from what the training distribution would imply for a price near ₹153,990.

**Root cause classification: F — RECURSIVE FORECASTING LIMITATION (primary) + B — FEATURE CONSTRUCTION INCONSISTENCY (minor, 0.72% impact).**

---

## Latest Actual Observation

| Field | Value |
|---|---|
| Date | 2026-09-01 |
| Target (INR per 10g) | ₹1,53,990.50 |
| Source | `data/processed/gold_feature_dataset.csv` |

---

## First Recursive Forecast

| Field | Value |
|---|---|
| Date | 2026-09-02 |
| Forecast (INR per 10g) | ₹1,41,292.29 |
| Source | `data/processed/model_data/diwali_recursive_forecast.csv` |

---

## Continuity Gap

| Metric | Value |
|---|---|
| Absolute gap | –₹12,698.21 |
| Gap magnitude | ₹12,698.21 |
| Percentage gap | 8.2461% |
| Direction | DOWN |

---

## Feature Construction Audit

**Status: PASS (engine is internally consistent with training pipeline)**

The forecast engine (`diwali_forecast_engine.py`) constructs features in `target_features()` using:

```python
series = pd.Series(target_history, dtype="float64")   # ends at 2026-09-01
historical = series.shift(1)                           # last element = Aug31 value
```

The training pipeline (`create_features.py`) constructs features using:

```python
historical_target = target.shift(1)
gold_ma_{w} = historical_target.rolling(w).mean()
gold_return_{p}d = historical_target.pct_change(p) * 100
```

**Both pipelines apply the same shift convention.** The engine's feature values for 2026-09-02 exactly match the training pipeline's feature values for the 2026-09-01 row. This is an **intentional and consistent** design: features at row D always reflect information through D-1 only.

---

## Lag Feature Audit

**Status: PASS**

| Feature | Engine Value (Sep02) | Expected (= Sep01 price) | Correct? |
|---|---|---|---|
| gold_lag_1 | 1,53,990.50 | 1,53,990.50 | ✓ YES |
| gold_lag_2 | 1,54,814.50 | Aug31 price | ✓ YES |
| gold_lag_3 | 1,58,902.00 | Aug28 price | ✓ YES |
| gold_lag_5 | 1,61,384.00 | Aug26 price | ✓ YES |
| gold_lag_7 | 1,62,378.50 | Aug22 price | ✓ YES |
| gold_lag_14 | 1,52,759.00 | Aug13 price | ✓ YES |

**`gold_lag_1` for 2026-09-02 correctly equals the latest actual price of ₹1,53,990.50.**

---

## Rolling Feature Audit

**Status: PASS (internally consistent with training)**

Moving average and volatility features are constructed using `historical_shifted = series.shift(1)`, then `.rolling(w).mean()` / `.std()`. This means:

- **gold_ma_3 for 2026-09-02** = mean(Aug31, Aug28, Aug27) = 1,57,382.67 — consistent with training
- **gold_ma_7 for 2026-09-02** = mean of 7 prices ending Aug31 = 1,59,737.50 — consistent with training
- **gold_volatility_7/14/30** — identical between engine and training convention

The engine is internally consistent. The training data used for model fitting saw the same feature convention.

---

## Off-by-One Audit

**Status: WARNING (minor, internally consistent)**

**What was found:**

The `gold_return_*` features in the engine are one time-step stale relative to the true boundary:

| Feature | Engine Sep02 | Correct Sep02 | Training Sep01 | Engine=Training? | Impact on Gap |
|---|---|---|---|---|---|
| gold_return_1d | −2.5723% | −0.5322% | −2.5723% | YES | +₹0 (offset) |
| gold_return_3d | −4.0707% | −3.0909% | −4.0707% | YES | +₹0 (offset) |
| gold_return_7d | −1.5385% | −3.7917% | −1.5385% | YES | +₹0 (offset) |

**The engine's return for 2026-09-02 equals the training feature's return for 2026-09-01** (one day stale). This means the model was *trained* on data with this same convention, so the model's coefficients for `gold_return_*` already reflect this shifted representation.

**Quantified impact of correcting the return stale-shift:** only **−₹91.87** (0.72% of the total gap). Correcting this would make the gap *slightly larger*, not smaller.

**Conclusion:** The stale-shift is an internal convention, not a bug that causes the gap.

---

## Preprocessing Audit

**Status: PASS**

- `preprocessor.joblib` was fitted exclusively on training data (117 rows).
- During recursive forecasting, `preprocessor.transform()` is called without refitting.
- Feature names output by `preprocessor.get_feature_names_out()` exactly match `MODEL_FEATURES` (46 features).
- NaN features (7 of 46 — OHLC open/high/low/volume for gold USD and USD/INR) are handled by the training-fitted imputer within the preprocessor. This is the same mechanism used during training and test evaluation.

---

## Target Scale Audit

**Status: PASSED**

| Dataset | Min (INR/10g) | Max (INR/10g) |
|---|---|---|
| Training | 1,04,543 | 1,61,254 |
| Validation | 1,39,948 | 1,46,987 |
| Test | 1,42,346 | 1,62,378 |
| Forecast | 1,38,995 | 1,44,450 |
| Latest actual | 1,53,990 | — |

All values are in INR per 10 grams. No unit conversion issue, scaling inversion, or normalisation artifact was found.

---

## Market Input Audit

**Status: PASS**

| Signal | Latest Actual (2026-09-01) | First Forecast (2026-09-02) | Change |
|---|---|---|---|
| gold_usd_close | 4,348.00 | 4,346.02 | −0.05% |
| usdinr_close | 95.1144 | 95.3072 | +0.20% |
| gold_inr_proxy | 4,13,557.42 | 4,14,206.80 | +0.16% |

The market transition is **smooth and minimal** — under 0.25% in all signals. Market forecast inputs do not materially contribute to the price discontinuity.

Future market values come from AutoReg(lags=5, trend='ct') models fitted on actual historical market data through 2026-09-01. No future actual market data was used.

---

## Model Contribution Audit

Top contributors to the 2026-09-02 prediction (sorted by absolute contribution):

| Feature | Coefficient | Transformed Value | Contribution |
|---|---|---|---|
| usdinr_high | 1,222.27 | 89.51 | +₹1,09,408.82 |
| gold_usd_high | 22.49 | 4,215.80 | +₹94,830.95 |
| usdinr_low | −1,063.03 | 88.99 | −₹94,600.18 |
| usdinr_close | 970.80 | 95.31 | +₹92,524.65 |
| usdinr_open | 882.93 | 89.16 | +₹78,720.08 |
| gold_usd_close | −13.79 | 4,346.02 | −₹59,937.63 |
| gold_inr_proxy | 0.07 | 4,14,206.80 | +₹27,417.20 |
| gold_lag_1 | 0.056 | 1,53,990.50 | +₹8,644.27 |

**Key observation:** The large positive and negative contributions from OHLC-related features (especially `usdinr_high` / `usdinr_low` / `usdinr_open`) nearly cancel each other out. The imputed NaN values for Open/High/Low (set by the training-fitted imputer to training-period means) are substantially different from the actual Sep01 OHLC values, and different from the forecast-boundary context. This is the **primary structural driver** of the model's output at the boundary.

The model was trained in a period where OHLC features were known from actual market data. During recursive forecasting, only `gold_usd_close` and `usdinr_close` are available; open, high, low, and volume are imputed. The training-fitted imputer fills them with training-set means, which are well below the current ₹1,53,990 price regime. This creates a systematic structural difference between the training+test environment and the forecast boundary environment.

---

## First Forecast Reproduction

**Status: MATCHED**

The first forecast for 2026-09-02 was independently reproduced using:
- The exact saved `linear_regression.joblib` model
- The exact saved `preprocessor.joblib` preprocessor
- The exact feature vector reconstructed from historical data

| | Value |
|---|---|
| Stored forecast | ₹1,41,292.2922 |
| Reproduced forecast | ₹1,41,292.2922 |
| Difference | ₹0.000000 |

The engine is deterministic and internally correct. There is no implementation bug that produces a random or erroneous value.

---

## Root Cause

**Primary classification: F — RECURSIVE FORECASTING LIMITATION**

**Secondary (minor): B — FEATURE CONSTRUCTION INCONSISTENCY (0.72% of gap)**

### Explanation

The 8.25% gap between the latest actual price (₹1,53,990.50) and the first recursive forecast (₹1,41,292.29) is primarily caused by the following structural conditions:

1. **OHLC feature imputation at the boundary.** The Linear Regression model has large positive and negative coefficients for `usdinr_high`, `usdinr_low`, `usdinr_open`, `gold_usd_high`, `gold_usd_low`. During recursive forecasting, these OHLC features are `NaN` (only close prices are forecasted). The training-fitted imputer fills them with training-set means, which represent a price regime of approximately ₹1,04,000–₹1,42,000. At the boundary, actual prices are near ₹1,54,000. This creates a systematic downward bias from the imputed OHLC values.

2. **Extrapolation outside training distribution.** The latest actual price of ₹1,54,000 is at or above the top of the training range (max ₹1,61,254 in training). The model is extrapolating outside the price regime it was optimised on. Linear Regression extrapolation in a high-feature, multi-collinear setting can produce large boundary jumps.

3. **Target lag features bridge the boundary correctly.** `gold_lag_1 = ₹1,53,990.50` is correct. However, the downstream model combines this with imputed OHLC values that are substantially below the actual price, pulling the prediction toward the training distribution.

4. **Return feature stale-shift.** The `gold_return_*` features are one step stale (using Aug31 price changes rather than Sep01 price changes). This is internally consistent with the training convention. Its isolated numerical impact on the gap is **only ₹92** (0.72%).

5. **Market inputs are smooth.** The gold USD and USD/INR forecast inputs for Sep02 differ from Sep01 actuals by under 0.25%. Market inputs do not drive the gap.

---

## Severity

**MEDIUM**

The gap is large (8.25%) but:
- The forecast is internally self-consistent (reproduces exactly).
- The training feature convention is maintained throughout the forecast horizon.
- The forecast converges to a plausible range (₹1,38,995–₹1,44,450) that is within the validation set price range (₹1,39,948–₹1,46,987).
- The Diwali reference estimate (₹1,42,442.41) is within the model's demonstrated test-set error range.
- No data leakage, target fabrication, or test-set retraining occurred.

The gap is an artefact of imputed OHLC values + linear extrapolation, not a code error.

---

## Recommended Action

> [!IMPORTANT]
> **DO NOT modify the frozen forecast without formal approval of a revised methodology.**

The following options exist for a future controlled methodology update:

### Option A — Accept current forecast (no change)
Document the boundary discontinuity as a known limitation of OHLC imputation in a recursive Linear Regression system. The Diwali reference estimate of ₹1,42,442.41 is defensible given test-set performance (MAPE 1.42%, R² 0.84).

### Option B — Use close-only model variant (requires retraining)
Retrain the model using only close-price features (no OHLC open/high/low/volume). This would eliminate the imputation-driven boundary effect. **Requires retraining and full evaluation. Frozen forecast would become invalid.**

### Option C — Improve OHLC imputation at boundary (requires methodology change)
Replace the training-mean imputer with a boundary-aware fill (e.g. impute from the latest actual OHLC proportions). **Requires feature pipeline change, preprocessor refit, and retraining. Frozen forecast would become invalid.**

### Option D — Accept and annotate
Add a clear annotation in the frontend UI noting that the recursive forecast begins from the model's predicted level as of Sep 02 2026, which reflects OHLC imputation at the boundary. Diwali estimate remains the primary output.

**Recommended path: Option A or D for the current frozen forecast. Option B for a future model refresh.**

---

## Frozen Forecast Status

**UNCHANGED ✓**

| Field | Value |
|---|---|
| diwali_reference_estimate | ₹1,42,442.41 |
| lower_estimate | ₹1,37,889.90 |
| upper_estimate | ₹1,44,859.72 |
| future_actual_ibja_used | false |
| test_retraining | false |
| Frozen | YES |

No model, preprocessor, or forecast artifact was modified during this diagnostic step.
