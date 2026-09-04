# Step 40.1 — Return Feature Correction Report

**Date:** 2026-09-03  
**Project:** Gold Price Intelligence — Gold Price Prediction System during Diwali 2026  
**Scope:** Technical investigation & safe correction experiment for recursive return-feature semantics.

---

## Existing Issue

During the Step 40 Forecast Continuity Diagnostic, a minor feature-construction inconsistency was identified between the training pipeline and the recursive forecast engine:
- **`gold_return_1d`**, **`gold_return_3d`**, and **`gold_return_7d`** in the forecast engine were calculated from a series that was shifted an additional step prior to taking percentage changes.
- This caused return features during recursive forecasting to be **one time-step stale** (e.g. for the 2026-09-02 forecast date, the engine used price returns from Aug 28 → Aug 31 instead of Aug 31 → Sep 01).
- The estimated isolated impact on the first forecast step was approximately **−₹91.87 to −₹97.47** (~0.72% of the overall continuity gap).

---

## Training Feature Semantics

In `src/features/create_features.py`, training features are constructed across historical rows:

```python
historical_target = target.shift(1)
features["gold_return_1d"] = historical_target.pct_change(periods=1) * 100
features["gold_return_3d"] = historical_target.pct_change(periods=3) * 100
features["gold_return_7d"] = historical_target.pct_change(periods=7) * 100
```

For any given historical date $D$:
- `historical_target[D]` $= \text{target}[D-1]$
- `gold_return_1d[D]` $= \frac{\text{target}[D-1] - \text{target}[D-2]}{\text{target}[D-2]} \times 100$

Thus, at target date $D$, the return feature reflects the percentage price change from day $D-2$ to day $D-1$ (the most recently completed business day).

---

## Recursive Feature Semantics

In `src/models/diwali_forecast_engine.py`, target features during recursive forecasting were constructed using:

```python
series = pd.Series(target_history, dtype="float64")  # ends at D-1
historical = series.shift(1)                          # last element = D-2
result["gold_return_1d"] = historical.pct_change(periods=1).iloc[-1] * 100
```

For recursive forecast date $D$:
- `target_history` contains observed and predicted prices through $D-1$.
- `series.iloc[-1]` $= \text{target}[D-1]$.
- However, `historical = series.shift(1)` caused `historical.iloc[-1]` to equal $\text{target}[D-2]$.
- Consequently, `historical.pct_change(1).iloc[-1]` calculated:
  $$\frac{\text{target}[D-2] - \text{target}[D-3]}{\text{target}[D-3]} \times 100$$
- This was one business day behind the training pipeline semantics.

---

## Root Cause

The root cause was **double-shifting in `target_features()`**. 

Because `target_history` already terminates at $D-1$ (since future target values past $D-1$ are not yet known), taking `.iloc[-1]` from `series` directly provides the observation at $D-1$. Applying `series.shift(1)` prior to `.pct_change()` introduced an unnecessary second shift.

---

## Corrected Logic

The correction removes the extra shift specifically for return feature calculations:

```python
def corrected_target_features(target_history: list[float]) -> dict[str, float]:
    series = pd.Series(target_history, dtype="float64")
    historical = series.shift(1)  # retained for MAs and volatility
    result: dict[str, float] = {}
    for lag in (1, 2, 3, 5, 7, 14):
        result[f"gold_lag_{lag}"] = series.iloc[-lag] if len(series) >= lag else np.nan
    for window in (3, 7, 14, 30):
        result[f"gold_ma_{window}"] = historical.tail(window).mean() if len(historical.dropna()) >= window else np.nan
    # CORRECTED: use series directly for pct_change
    for period in (1, 3, 7):
        result[f"gold_return_{period}d"] = series.pct_change(periods=period).iloc[-1] * 100 if len(series) > period else np.nan
    returns = historical.pct_change() * 100
    for window in (7, 14, 30):
        result[f"gold_volatility_{window}"] = returns.tail(window).std() if len(returns.dropna()) >= window else np.nan
    return result
```

With this change:
- `gold_return_1d` at recursive date $D$ $= \frac{\text{target}[D-1] - \text{target}[D-2]}{\text{target}[D-2]} \times 100$, exactly matching the training feature definition.

---

## Leakage Verification

- **Future Target Data:** `series` contains values up to index $-1$, corresponding strictly to $D-1$. No target at date $D$ or beyond is used.
- **Future Market Data:** Market features rely solely on forecasted exogenous inputs or historical market closes through $D-1$.
- **Test Set Information:** No test-set target observations are accessed.
- **Conclusion:** **LEAKAGE CHECK PASSED.** The corrected logic is completely leakage-safe.

---

## Forecast Comparison

A full 49-business-day recursive forecast comparison was performed between the old engine logic and the corrected logic:

- **Artifact generated:** `reports/step40_1_forecast_comparison.csv`
- **Temporary forecast artifact:** `reports/step40_1_corrected_recursive_forecast.csv`

### Summary Statistics across all 49 Forecast Days:
| Metric | Value |
|---|---|
| Max Absolute Difference | ₹1,348.97 |
| Mean Absolute Difference | ₹158.28 |
| Min Absolute Difference | ₹1.13 |

---

## First Forecast Comparison

For **2026-09-02** (first forecast date):

| Version | Forecast (INR per 10g) |
|---|---|
| Old Engine | ₹1,41,292.29 |
| Corrected Logic | ₹1,41,194.82 |
| **Difference** | **−₹97.47 (−0.0690%)** |

Independent single-step reproduction of the corrected prediction matched to **₹0.000000**.

---

## Diwali Forecast Comparison

For **2026-11-08** (Diwali reference estimate interpolated between Nov 06 and Nov 09):

| Version | Previous Business Day (2026-11-06) | Next Business Day (2026-11-09) | Diwali Reference (2026-11-08) |
|---|---|---|---|
| Old Engine (Frozen) | ₹1,42,180.23 | ₹1,42,704.58 | **₹1,42,442.41** |
| Corrected Logic | ₹1,42,179.10 | ₹1,42,615.16 | **₹1,42,397.13** |
| **Difference** | **−₹1.13** | **−₹89.42** | **−₹45.28 (−0.0318%)** |

---

## Forecast Range Comparison

Using the 5th and 95th residual quantiles (−₹4,552.51 to +₹2,417.31):

| Version | Lower Estimate (5th percentile) | Upper Estimate (95th percentile) |
|---|---|---|
| Old Engine (Frozen) | ₹1,37,889.90 | ₹1,44,859.72 |
| Corrected Logic | ₹1,37,844.62 | ₹1,44,814.45 |
| **Difference** | **−₹45.28** | **−₹45.28** |

---

## Model Integrity

- **Selected Model:** Linear Regression
- **Model Retrained:** NO (`models/linear_regression.joblib` untouched)
- **Preprocessor Refit:** NO (`data/processed/model_data/preprocessor.joblib` untouched)

---

## Frozen Forecast Integrity

- **`models/final_diwali_forecast.json`** was verified before and after the experiment.
- **Status:** **UNCHANGED ✓**
- Authoritative reference estimate remains **₹142,442.41**.

---

## Recommendation

1. **Materiality Assessment:** The impact on the Diwali reference forecast is **−₹45.28 (−0.0318%)**, which is far below the model's test MAE of ₹2,122.61. The change is **NEGLIGIBLE**.
2. **Action Recommendation:**
   - Adopt the corrected `target_features()` logic in `src/models/diwali_forecast_engine.py` for any future code updates.
   - Keep the existing frozen Diwali forecast (`models/final_diwali_forecast.json`) authoritative unless explicit model/forecast regeneration is ordered in a subsequent step.
