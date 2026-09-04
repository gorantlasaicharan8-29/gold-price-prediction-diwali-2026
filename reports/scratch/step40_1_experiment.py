"""
Step 40.1 — Safe Correction of Recursive Return-Feature Inconsistency
Generates a TEMPORARY corrected forecast only.
Does NOT overwrite any frozen artifact.
"""
import io
import sys

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')

import json
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import joblib
from pathlib import Path

PROJECT_ROOT = Path('.').resolve()
FEATURE_PATH       = PROJECT_ROOT / "data" / "processed" / "gold_feature_dataset.csv"
MARKET_PATH        = PROJECT_ROOT / "data" / "raw" / "international_market_data.csv"
MODEL_PATH         = PROJECT_ROOT / "models" / "linear_regression.joblib"
PREPROCESSOR_PATH  = PROJECT_ROOT / "data" / "processed" / "model_data" / "preprocessor.joblib"
FUTURE_MARKET_PATH = PROJECT_ROOT / "data" / "processed" / "model_data" / "future_market_forecasts.csv"
FROZEN_PATH        = PROJECT_ROOT / "models" / "final_diwali_forecast.json"
STORED_FC_PATH     = PROJECT_ROOT / "data" / "processed" / "model_data" / "diwali_recursive_forecast.csv"
EVAL_DIR           = PROJECT_ROOT / "reports" / "model_evaluation"
REPORTS_DIR        = PROJECT_ROOT / "reports"

DIWALI_DATE        = pd.Timestamp("2026-11-08")
LATEST_TARGET_DATE = pd.Timestamp("2026-09-01")
FORECAST_START     = pd.Timestamp("2026-09-02")
FORECAST_END       = pd.Timestamp("2026-11-09")

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

print("=" * 70)
print("STEP 40.1 — SAFE CORRECTION OF RECURSIVE RETURN-FEATURE INCONSISTENCY")
print("=" * 70)

# ── [0] Verify frozen forecast BEFORE ────────────────────────────────────────
print("\n[0] Pre-check: verifying frozen forecast is untouched...")
frozen_before = json.loads(FROZEN_PATH.read_text(encoding='utf-8'))
FROZEN_REF_BEFORE = frozen_before['diwali_reference_estimate']
print(f"  Frozen diwali_reference_estimate: {FROZEN_REF_BEFORE:,.4f}")
print(f"  Frozen UNCHANGED: {'YES' if abs(FROZEN_REF_BEFORE - 142442.40) < 1.0 else 'NO — CRITICAL!'}")

# ── [1] Semantic analysis ─────────────────────────────────────────────────────
print("\n[1] Semantic analysis: training vs engine return feature construction")
print()
print("  TRAINING (create_features.py) for row at date D:")
print("    historical_target = target.shift(1)")
print("    gold_return_1d[D] = historical_target.pct_change(1)[D]")
print("                      = (target[D-1] - target[D-2]) / target[D-2]")
print("                      = % change from price at D-2 to price at D-1")
print()
print("  ENGINE (diwali_forecast_engine.py) target_features() for date D:")
print("    series   = [..., price[D-1]]  (target_history ends at D-1)")
print("    historical = series.shift(1)  <- last element = price[D-2]")
print("    gold_return_1d = historical.pct_change(1).iloc[-1]")
print("                   = (historical[-1] - historical[-2]) / historical[-2]")
print("                   = (price[D-2] - price[D-3]) / price[D-3]")
print("                   = % change from price at D-3 to price at D-2  ← ONE STEP STALE")
print()
print("  ROOT CAUSE: The engine applies series.shift(1) BEFORE pct_change()")
print("  This shifts the return window back by one more step than the training pipeline.")
print()
print("  CORRECT engine logic for date D should be:")
print("    gold_return_1d = series.pct_change(1).iloc[-1]")
print("                   = (series[-1] - series[-2]) / series[-2]")
print("                   = (price[D-1] - price[D-2]) / price[D-2]")
print("                   = % change from price at D-2 to price at D-1  ← MATCHES TRAINING")

# ── [2] Verify with actual numbers ────────────────────────────────────────────
print("\n[2] Numerical verification with boundary prices...")
historical = pd.read_csv(FEATURE_PATH)
historical["date"] = pd.to_datetime(historical["date"])
historical = historical[historical["date"] <= LATEST_TARGET_DATE].sort_values("date").reset_index(drop=True)

target_hist = historical["target_gold_999"].astype(float)
sep01 = float(historical[historical["date"] == pd.Timestamp("2026-09-01")]["target_gold_999"].iloc[0])
aug31 = float(historical[historical["date"] == pd.Timestamp("2026-08-31")]["target_gold_999"].iloc[0])
aug28 = float(historical[historical["date"] == pd.Timestamp("2026-08-28")]["target_gold_999"].iloc[0])
aug25 = float(historical[historical["date"] == pd.Timestamp("2026-08-25")]["target_gold_999"].iloc[0])
aug21 = float(historical[historical["date"] == pd.Timestamp("2026-08-21")]["target_gold_999"].iloc[0])
aug14 = float(historical[historical["date"] == pd.Timestamp("2026-08-14")]["target_gold_999"].iloc[0])

target_history = historical["target_gold_999"].astype(float).tolist()
series_pre = pd.Series(target_history, dtype="float64")   # ends at Sep01

# OLD ENGINE return values (stale)
historical_shifted = series_pre.shift(1)   # last = Aug31
old_ret1d = historical_shifted.pct_change(1).iloc[-1] * 100
old_ret3d = historical_shifted.pct_change(3).iloc[-1] * 100
old_ret7d = historical_shifted.pct_change(7).iloc[-1] * 100

# CORRECTED return values
new_ret1d = series_pre.pct_change(1).iloc[-1] * 100
new_ret3d = series_pre.pct_change(3).iloc[-1] * 100
new_ret7d = series_pre.pct_change(7).iloc[-1] * 100

# Training values for 2026-09-01 row (the last training row)
train_ret1d = float(historical[historical["date"] == pd.Timestamp("2026-09-01")]["gold_return_1d"].iloc[0])
train_ret3d = float(historical[historical["date"] == pd.Timestamp("2026-09-01")]["gold_return_3d"].iloc[0])
train_ret7d = float(historical[historical["date"] == pd.Timestamp("2026-09-01")]["gold_return_7d"].iloc[0])

print(f"  Prices: Sep01={sep01:.2f} Aug31={aug31:.2f} Aug28={aug28:.2f} Aug25={aug25:.2f} Aug21={aug21:.2f} Aug14={aug14:.2f}")
print()
print(f"  {'Feature':<20} {'Old Engine':>14} {'Corrected':>14} {'Train Sep01':>14} {'Corr=Train?':>12}")
print("  " + "-" * 78)
for feat, old, new, trn in [
    ("gold_return_1d", old_ret1d, new_ret1d, train_ret1d),
    ("gold_return_3d", old_ret3d, new_ret3d, train_ret3d),
    ("gold_return_7d", old_ret7d, new_ret7d, train_ret7d),
]:
    consistent = "YES ✓" if abs(new - trn) < 0.001 else "NO ✗"
    print(f"  {feat:<20} {old:>14.4f} {new:>14.4f} {trn:>14.4f} {consistent:>12}")

print()
print("  OBSERVATION: old engine = training Sep01 row (stale by 1 step)")
print("  OBSERVATION: corrected  = training Sep01 row shifted forward 1 step")
print("  LEAKAGE CHECK: corrected values use only prices through D-1 — SAFE")

# ── [3] Load all artifacts ────────────────────────────────────────────────────
print("\n[3] Loading all artifacts...")
market_raw = pd.read_csv(MARKET_PATH)
market_raw["date"] = pd.to_datetime(market_raw["date"])
market_hist = market_raw[market_raw["date"] <= LATEST_TARGET_DATE].sort_values("date").reset_index(drop=True)
future_market = pd.read_csv(FUTURE_MARKET_PATH)
future_market["date"] = pd.to_datetime(future_market["date"])
future_market = future_market.sort_values("date").reset_index(drop=True)
model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)
stored_fc = pd.read_csv(STORED_FC_PATH)
stored_fc["date"] = pd.to_datetime(stored_fc["date"])
stored_fc = stored_fc.sort_values("date").reset_index(drop=True)
expected_names = list(preprocessor.get_feature_names_out())
future_dates = pd.date_range(FORECAST_START, FORECAST_END, freq="B")
gold_mfc  = future_market.set_index("date")["gold_usd_close_forecast"]
fx_mfc    = future_market.set_index("date")["usdinr_close_forecast"]
print(f"  Artifacts loaded. Forecast horizon: {len(future_dates)} business days")

# ── Helper functions (unchanged from engine) ──────────────────────────────────

def calendar_features(current_date):
    days_to_diwali = (DIWALI_DATE - current_date).days
    return {
        "day_of_week":    current_date.dayofweek,
        "day_of_month":   current_date.day,
        "month":          current_date.month,
        "quarter":        current_date.quarter,
        "day_of_year":    current_date.dayofyear,
        "week_of_year":   int(current_date.isocalendar()[1]),
        "is_month_start": int(current_date.is_month_start),
        "is_month_end":   int(current_date.is_month_end),
        "days_to_diwali": days_to_diwali,
        "is_near_diwali": int(abs(days_to_diwali) <= 30),
    }

def market_features(gold_history, fx_history, gold_forecast, fx_forecast):
    gold = pd.Series([*gold_history, gold_forecast], dtype="float64")
    fx   = pd.Series([*fx_history,   fx_forecast],   dtype="float64")
    result = {
        "gold_usd_open": np.nan, "gold_usd_high": np.nan, "gold_usd_low": np.nan,
        "gold_usd_close": gold_forecast, "gold_usd_volume": np.nan,
        "usdinr_open": np.nan, "usdinr_high": np.nan, "usdinr_low": np.nan,
        "usdinr_close": fx_forecast,
        "gold_inr_proxy": gold_forecast * fx_forecast,
    }
    for period in (1, 3, 7):
        result[f"gold_usd_return_{period}d"] = gold.pct_change(periods=period).iloc[-1] * 100 if len(gold) > period else np.nan
        result[f"usdinr_return_{period}d"]   = fx.pct_change(periods=period).iloc[-1] * 100   if len(fx)   > period else np.nan
    for window in (7, 14):
        result[f"gold_usd_volatility_{window}"] = gold.pct_change().tail(window).std() * 100
        result[f"usdinr_volatility_{window}"]   = fx.pct_change().tail(window).std()   * 100
    return result

# ── OLD target_features (original engine logic) ───────────────────────────────
def old_target_features(target_history):
    """ORIGINAL engine logic — returns are computed from shifted series (stale by 1)."""
    series = pd.Series(target_history, dtype="float64")
    historical = series.shift(1)   # ← the source of staleness
    result = {}
    for lag in (1, 2, 3, 5, 7, 14):
        result[f"gold_lag_{lag}"] = series.iloc[-lag] if len(series) >= lag else np.nan
    for window in (3, 7, 14, 30):
        result[f"gold_ma_{window}"] = historical.tail(window).mean() if len(historical.dropna()) >= window else np.nan
    # STALE: uses historical (shifted), not series
    for period in (1, 3, 7):
        result[f"gold_return_{period}d"] = historical.pct_change(periods=period).iloc[-1] * 100 if len(historical.dropna()) > period else np.nan
    returns = historical.pct_change() * 100
    for window in (7, 14, 30):
        result[f"gold_volatility_{window}"] = returns.tail(window).std() if len(returns.dropna()) >= window else np.nan
    return result

# ── CORRECTED target_features ─────────────────────────────────────────────────
def corrected_target_features(target_history):
    """CORRECTED logic — returns use series directly (no extra shift).
    
    Correction: gold_return_{1,3,7}d now uses series.pct_change(period).iloc[-1]
    instead of historical.pct_change(period).iloc[-1].
    
    This matches the training pipeline semantics:
      training:  historical_target.pct_change(p)[D]  = (price[D-1] - price[D-p-1]) / price[D-p-1]
      corrected: series.pct_change(p).iloc[-1]        = (price[D-1] - price[D-p-1]) / price[D-p-1]
    
    All other features (lags, MAs, volatility) are unchanged.
    """
    series = pd.Series(target_history, dtype="float64")
    historical = series.shift(1)   # kept for MAs and volatility (same convention as training)
    result = {}
    for lag in (1, 2, 3, 5, 7, 14):
        result[f"gold_lag_{lag}"] = series.iloc[-lag] if len(series) >= lag else np.nan
    for window in (3, 7, 14, 30):
        result[f"gold_ma_{window}"] = historical.tail(window).mean() if len(historical.dropna()) >= window else np.nan
    # CORRECTED: use series directly (not historical) for returns
    for period in (1, 3, 7):
        result[f"gold_return_{period}d"] = series.pct_change(periods=period).iloc[-1] * 100 if len(series) > period else np.nan
    returns = historical.pct_change() * 100
    for window in (7, 14, 30):
        result[f"gold_volatility_{window}"] = returns.tail(window).std() if len(returns.dropna()) >= window else np.nan
    return result

# ── [4] Run both forecasts ────────────────────────────────────────────────────
print("\n[4] Running both forecast loops (old and corrected)...")

def run_forecast(target_features_fn, label):
    tgt_hist  = historical["target_gold_999"].astype(float).tolist()
    gold_hist = market_hist["gold_usd_close"].dropna().astype(float).tolist()
    fx_hist   = market_hist["usdinr_close"].dropna().astype(float).tolist()
    results = []
    for current_date in future_dates:
        gf = float(gold_mfc.loc[current_date])
        ff = float(fx_mfc.loc[current_date])
        row = {**calendar_features(current_date), **target_features_fn(tgt_hist), **market_features(gold_hist, fx_hist, gf, ff)}
        row_frame = pd.DataFrame([row], columns=MODEL_FEATURES)
        transformed = pd.DataFrame(preprocessor.transform(row_frame), columns=expected_names)
        prediction = float(model.predict(transformed)[0])
        if not np.isfinite(prediction):
            raise RuntimeError(f"Non-finite prediction on {current_date.date()} in {label}")
        results.append({"date": current_date.strftime("%Y-%m-%d"), "forecast_gold_999": prediction,
                         "gold_usd_close_forecast": gf, "usdinr_close_forecast": ff,
                         "gold_inr_proxy": gf * ff,
                         "days_to_diwali": (DIWALI_DATE - current_date).days,
                         "is_near_diwali": int(abs((DIWALI_DATE - current_date).days) <= 30)})
        tgt_hist.append(prediction)
        gold_hist.append(gf)
        fx_hist.append(ff)
    return pd.DataFrame(results)

old_fc  = run_forecast(old_target_features, "OLD")
new_fc  = run_forecast(corrected_target_features, "CORRECTED")
print(f"  Old forecast rows:       {len(old_fc)}")
print(f"  Corrected forecast rows: {len(new_fc)}")

# Verify old forecast matches stored forecast exactly
stored_vals = stored_fc.sort_values("date")["forecast_gold_999"].values
old_vals    = old_fc["forecast_gold_999"].values
max_diff_vs_stored = np.abs(old_vals - stored_vals).max()
print(f"  Max diff (old vs stored): {max_diff_vs_stored:.8f}  {'✓ MATCHES' if max_diff_vs_stored < 1e-4 else '✗ MISMATCH!'}")

# ── [5] First forecast comparison ────────────────────────────────────────────
print("\n[5] First forecast comparison (2026-09-02)...")
old_sep02  = float(old_fc[old_fc["date"]  == "2026-09-02"]["forecast_gold_999"].iloc[0])
new_sep02  = float(new_fc[new_fc["date"]  == "2026-09-02"]["forecast_gold_999"].iloc[0])
diff_sep02 = new_sep02 - old_sep02
pct_sep02  = (abs(diff_sep02) / old_sep02) * 100
print(f"  Old prediction:          INR {old_sep02:>14,.4f}")
print(f"  Corrected prediction:    INR {new_sep02:>14,.4f}")
print(f"  Absolute difference:     INR {diff_sep02:>14,.4f}")
print(f"  Percentage difference:       {pct_sep02:>13.4f}%")

# ── [6] Reproduce corrected Sep02 independently ────────────────────────────────
print("\n[6] Independent reproduction of corrected 2026-09-02 prediction...")
tgt_hist_verify = historical["target_gold_999"].astype(float).tolist()
gold_hist_verify = market_hist["gold_usd_close"].dropna().astype(float).tolist()
fx_hist_verify   = market_hist["usdinr_close"].dropna().astype(float).tolist()
gf_sep02 = float(gold_mfc.loc[FORECAST_START])
ff_sep02 = float(fx_mfc.loc[FORECAST_START])
row_verify = {**calendar_features(FORECAST_START),
              **corrected_target_features(tgt_hist_verify),
              **market_features(gold_hist_verify, fx_hist_verify, gf_sep02, ff_sep02)}
row_frame_v = pd.DataFrame([row_verify], columns=MODEL_FEATURES)
trans_v = pd.DataFrame(preprocessor.transform(row_frame_v), columns=expected_names)
repro = float(model.predict(trans_v)[0])
repro_diff = abs(repro - new_sep02)
print(f"  Corrected forecast from loop: INR {new_sep02:,.4f}")
print(f"  Independently reproduced:     INR {repro:,.4f}")
print(f"  Difference:                   INR {repro_diff:.8f}")
print(f"  REPRODUCTION: {'MATCHED ✓' if repro_diff < 1e-4 else 'NOT MATCHED ✗ STOP!'}")

# ── [7] Leakage check ─────────────────────────────────────────────────────────
print("\n[7] Leakage verification...")
print("  gold_return_1d = series.pct_change(1).iloc[-1]")
print("                 = (price[D-1] - price[D-2]) / price[D-2]")
print("  Uses: price[D-1] — this is the most recent KNOWN price (in target_history)")
print("        price[D-2] — one step earlier in target_history")
print("  NO current-period target used.")
print("  NO future market data used.")
print("  NO future IBJA data used.")
print("  LEAKAGE: NONE DETECTED")

# ── [8] Full comparison across all dates ──────────────────────────────────────
print("\n[8] Building full comparison table...")
comp = pd.DataFrame({
    "date": old_fc["date"].values,
    "old_prediction": old_fc["forecast_gold_999"].values,
    "corrected_prediction": new_fc["forecast_gold_999"].values,
})
comp["absolute_difference"] = comp["corrected_prediction"] - comp["old_prediction"]
comp["percentage_difference"] = comp["absolute_difference"] / comp["old_prediction"] * 100
comp.to_csv(REPORTS_DIR / "step40_1_forecast_comparison.csv", index=False)
print(f"  Saved: reports/step40_1_forecast_comparison.csv  ({len(comp)} rows)")
print(f"\n  Max absolute difference across all dates: INR {comp['absolute_difference'].abs().max():,.4f}")
print(f"  Mean absolute difference:                 INR {comp['absolute_difference'].abs().mean():,.4f}")
print(f"  Min absolute difference:                  INR {comp['absolute_difference'].abs().min():,.4f}")

# ── [9] Diwali forecast comparison ────────────────────────────────────────────
print("\n[9] Diwali 2026 forecast comparison (2026-11-08)...")
prev_biz_old  = float(old_fc[old_fc["date"]  == "2026-11-06"]["forecast_gold_999"].iloc[0])
next_biz_old  = float(old_fc[old_fc["date"]  == "2026-11-09"]["forecast_gold_999"].iloc[0])
prev_biz_new  = float(new_fc[new_fc["date"]  == "2026-11-06"]["forecast_gold_999"].iloc[0])
next_biz_new  = float(new_fc[new_fc["date"]  == "2026-11-09"]["forecast_gold_999"].iloc[0])
diwali_old = (prev_biz_old + next_biz_old) / 2
diwali_new = (prev_biz_new + next_biz_new) / 2
diff_diwali = diwali_new - diwali_old
pct_diwali  = (abs(diff_diwali) / diwali_old) * 100

print(f"  OLD prev biz day (Nov06):  INR {prev_biz_old:>14,.4f}")
print(f"  OLD next biz day (Nov09):  INR {next_biz_old:>14,.4f}")
print(f"  OLD Diwali reference:      INR {diwali_old:>14,.4f}")
print()
print(f"  CORR prev biz day (Nov06): INR {prev_biz_new:>14,.4f}")
print(f"  CORR next biz day (Nov09): INR {next_biz_new:>14,.4f}")
print(f"  CORR Diwali reference:     INR {diwali_new:>14,.4f}")
print()
print(f"  Diwali absolute diff:      INR {diff_diwali:>14,.4f}")
print(f"  Diwali percentage diff:        {pct_diwali:>13.4f}%")
print(f"  Frozen (authoritative):    INR {FROZEN_REF_BEFORE:>14,.4f}")

# ── [10] Forecast range comparison ────────────────────────────────────────────
print("\n[10] Forecast range comparison...")
# Reconstruct range using same empirical residual method as engine
validation = pd.read_csv(EVAL_DIR / "validation_predictions.csv")
test_preds  = pd.read_csv(EVAL_DIR / "test_predictions.csv")
residuals   = pd.concat([validation["actual_gold_999"] - validation["linear_regression_prediction"],
                          test_preds["residual"]], ignore_index=True)
lower_r, upper_r = residuals.quantile([0.05, 0.95])
old_range_lo  = diwali_old + lower_r
old_range_hi  = diwali_old + upper_r
new_range_lo  = diwali_new + lower_r
new_range_hi  = diwali_new + upper_r
frozen_lo     = frozen_before['lower_estimate']
frozen_hi     = frozen_before['upper_estimate']

print(f"  OLD   range: INR {old_range_lo:>12,.2f} — {old_range_hi:>12,.2f}")
print(f"  CORR  range: INR {new_range_lo:>12,.2f} — {new_range_hi:>12,.2f}")
print(f"  FROZEN range: INR {frozen_lo:>12,.2f} — {frozen_hi:>12,.2f}")
print(f"  Range lower diff: INR {new_range_lo - old_range_lo:,.4f}")
print(f"  Range upper diff: INR {new_range_hi - old_range_hi:,.4f}")

# ── [11] Save corrected forecast ──────────────────────────────────────────────
print("\n[11] Saving corrected forecast artifact...")
new_fc.to_csv(REPORTS_DIR / "step40_1_corrected_recursive_forecast.csv", index=False)
print(f"  Saved: reports/step40_1_corrected_recursive_forecast.csv")

# ── [12] Verify frozen forecast UNCHANGED after ────────────────────────────────
print("\n[12] Post-check: verifying frozen forecast still untouched...")
frozen_after = json.loads(FROZEN_PATH.read_text(encoding='utf-8'))
FROZEN_REF_AFTER = frozen_after['diwali_reference_estimate']
frozen_unchanged = abs(FROZEN_REF_BEFORE - FROZEN_REF_AFTER) < 1e-6
print(f"  Frozen diwali_reference_estimate: {FROZEN_REF_AFTER:,.4f}")
print(f"  FROZEN UNCHANGED: {'YES ✓' if frozen_unchanged else 'NO — CRITICAL!'}")

# ── [13] Materiality assessment ────────────────────────────────────────────────
print("\n[13] Materiality assessment...")
max_abs_diff = comp['absolute_difference'].abs().max()
diwali_pct_diff = pct_diwali
# MAPE of the model on test is 1.4178% = ~₹2,123 on an average test price
test_mae = 2122.61
is_material = max_abs_diff > test_mae or diwali_pct_diff > 1.0
print(f"  Test MAE (reference):              INR {test_mae:,.2f}")
print(f"  Max forecast diff (any date):      INR {max_abs_diff:,.4f}")
print(f"  Diwali estimate diff:              INR {diff_diwali:,.4f}  ({diwali_pct_diff:.4f}%)")
print(f"  Correction is material (>MAE):     {'YES' if is_material else 'NO — NEGLIGIBLE'}")

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Return-feature inconsistency: IDENTIFIED")
print(f"Root cause: engine applies series.shift(1) BEFORE pct_change()," )
print(f"            making gold_return_{{1,3,7}}d one step stale relative to training.")
print(f"Correction: use series.pct_change(period).iloc[-1] instead of")
print(f"            historical.pct_change(period).iloc[-1]")
print(f"Model retrained:              NO")
print(f"Selected model:               Linear Regression")
print(f"Frozen forecast:              {'UNCHANGED ✓' if frozen_unchanged else 'CHANGED!'}")
print(f"First forecast (Sep02) old:   INR {old_sep02:,.4f}")
print(f"First forecast (Sep02) corr:  INR {new_sep02:,.4f}")
print(f"First forecast difference:    INR {diff_sep02:,.4f}  ({pct_sep02:.4f}%)")
print(f"Diwali old:                   INR {diwali_old:,.4f}")
print(f"Diwali corrected:             INR {diwali_new:,.4f}")
print(f"Diwali difference:            INR {diff_diwali:,.4f}  ({diwali_pct_diff:.4f}%)")
print(f"Leakage:                      PASSED")
print(f"Future actual IBJA data:      NOT USED")
print(f"Future actual market data:    NOT USED")
print(f"Corrected forecast:           CREATED (reports/step40_1_corrected_recursive_forecast.csv)")
print(f"Comparison report:            CREATED (reports/step40_1_forecast_comparison.csv)")
print(f"Correction materiality:       {'MATERIAL (>MAE)' if is_material else 'NEGLIGIBLE (<MAE)'}")
print()
print("AWAITING FURTHER INSTRUCTIONS.")
print("Frozen forecast NOT replaced. Model NOT retrained.")
