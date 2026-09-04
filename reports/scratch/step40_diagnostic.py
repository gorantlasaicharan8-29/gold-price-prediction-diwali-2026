"""
Step 40 — Forecast Continuity Diagnostic Script
Reads all existing artifacts. Does NOT modify any file.
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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEATURE_PATH    = PROJECT_ROOT / "data" / "processed" / "gold_feature_dataset.csv"
MARKET_PATH     = PROJECT_ROOT / "data" / "raw" / "international_market_data.csv"
MODEL_PATH      = PROJECT_ROOT / "models" / "linear_regression.joblib"
PREPROCESSOR_PATH = PROJECT_ROOT / "data" / "processed" / "model_data" / "preprocessor.joblib"
FORECAST_PATH   = PROJECT_ROOT / "data" / "processed" / "model_data" / "diwali_recursive_forecast.csv"
FUTURE_MARKET_PATH = PROJECT_ROOT / "data" / "processed" / "model_data" / "future_market_forecasts.csv"
FROZEN_PATH     = PROJECT_ROOT / "models" / "final_diwali_forecast.json"
REPORTS_DIR     = PROJECT_ROOT / "reports"
EVAL_DIR        = REPORTS_DIR / "model_evaluation"

DIWALI_DATE       = pd.Timestamp("2026-11-08")
LATEST_TARGET_DATE = pd.Timestamp("2026-09-01")
FORECAST_START    = pd.Timestamp("2026-09-02")

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
print("STEP 40 — FORECAST CONTINUITY DIAGNOSTIC")
print("=" * 70)

# ── 1. Load all artifacts ────────────────────────────────────────────────────
print("\n[1] Loading artifacts...")
historical = pd.read_csv(FEATURE_PATH)
historical["date"] = pd.to_datetime(historical["date"])
historical = historical[historical["date"] <= LATEST_TARGET_DATE].sort_values("date").reset_index(drop=True)

market_raw = pd.read_csv(MARKET_PATH)
market_raw["date"] = pd.to_datetime(market_raw["date"])
market_hist = market_raw[market_raw["date"] <= LATEST_TARGET_DATE].sort_values("date").reset_index(drop=True)

model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)
stored_forecast = pd.read_csv(FORECAST_PATH)
stored_forecast["date"] = pd.to_datetime(stored_forecast["date"])
stored_forecast = stored_forecast.sort_values("date").reset_index(drop=True)
future_market = pd.read_csv(FUTURE_MARKET_PATH)
future_market["date"] = pd.to_datetime(future_market["date"])
future_market = future_market.sort_values("date").reset_index(drop=True)
with open(FROZEN_PATH, encoding="utf-8") as f:
    frozen = json.load(f)

print(f"  Historical rows (up to {LATEST_TARGET_DATE.date()}): {len(historical)}")
print(f"  Market history rows:       {len(market_hist)}")
print(f"  Stored forecast rows:      {len(stored_forecast)}")
print(f"  Future market rows:        {len(future_market)}")

# ── 2. Latest actual observation ────────────────────────────────────────────
print("\n[2] Latest actual observation...")
latest_row = historical[historical["date"] == LATEST_TARGET_DATE]
assert not latest_row.empty, "CRITICAL: 2026-09-01 not in historical dataset!"
latest_actual_price = float(latest_row["target_gold_999"].iloc[0])
print(f"  Date:  {LATEST_TARGET_DATE.date()}")
print(f"  Price: INR {latest_actual_price:,.4f}")

# ── 3. First forecast ────────────────────────────────────────────────────────
print("\n[3] First recursive forecast...")
first_fc_row = stored_forecast[stored_forecast["date"] == FORECAST_START]
assert not first_fc_row.empty, "CRITICAL: 2026-09-02 not in stored forecast!"
first_fc_price = float(first_fc_row["forecast_gold_999"].iloc[0])
print(f"  Date:  {FORECAST_START.date()}")
print(f"  Price: INR {first_fc_price:,.4f}")

gap_abs = first_fc_price - latest_actual_price
gap_pct = (abs(gap_abs) / latest_actual_price) * 100
print(f"\n  Absolute gap:    INR {gap_abs:,.4f}")
print(f"  Gap magnitude:   INR {abs(gap_abs):,.4f}")
print(f"  Percentage gap:  {gap_pct:.6f}%")
print(f"  Direction:       {'DOWN' if gap_abs < 0 else 'UP'}")

# ── 4. Feature construction for 2026-09-02 (ENGINE logic) ───────────────────
print("\n[4] Reconstructing feature vector for 2026-09-02 using ENGINE logic...")

target_history = historical["target_gold_999"].astype(float).tolist()
gold_history   = market_hist["gold_usd_close"].dropna().astype(float).tolist()
fx_history     = market_hist["usdinr_close"].dropna().astype(float).tolist()

# --- Replicate calendar_features() ---
current_date = FORECAST_START
days_to_diwali = (DIWALI_DATE - current_date).days if pd.notna(current_date) else np.nan
calendar_feats = {
    "day_of_week":    current_date.dayofweek if pd.notna(current_date) else np.nan,
    "day_of_month":   current_date.day if pd.notna(current_date) else np.nan,
    "month":          current_date.month if pd.notna(current_date) else np.nan,
    "quarter":        current_date.quarter if pd.notna(current_date) else np.nan,
    "day_of_year":    current_date.dayofyear if pd.notna(current_date) else np.nan,
    # pyrefly: ignore [missing-attribute]
    "week_of_year":   int(current_date.isocalendar()[1]) if pd.notna(current_date) else np.nan,
    "is_month_start": int(current_date.is_month_start) if pd.notna(current_date) else np.nan,
    "is_month_end":   int(current_date.is_month_end) if pd.notna(current_date) else np.nan,
    "days_to_diwali": days_to_diwali,
    "is_near_diwali": int(abs(days_to_diwali) <= 30) if pd.notna(days_to_diwali) else np.nan,
}
print(f"  Calendar: days_to_diwali={days_to_diwali}, is_near_diwali={calendar_feats['is_near_diwali']}")

# --- Replicate target_features() EXACTLY as in the engine ---
# CRITICAL: the engine does series.shift(1) before computing rolling features
series = pd.Series(target_history, dtype="float64")
historical_shifted = series.shift(1)   # ← this is what engine calls 'historical'

engine_target_feats = {}
for lag in (1, 2, 3, 5, 7, 14):
    engine_target_feats[f"gold_lag_{lag}"] = series.iloc[-lag] if len(series) >= lag else np.nan
for window in (3, 7, 14, 30):
    engine_target_feats[f"gold_ma_{window}"] = historical_shifted.tail(window).mean() if len(historical_shifted.dropna()) >= window else np.nan
for period in (1, 3, 7):
    engine_target_feats[f"gold_return_{period}d"] = historical_shifted.pct_change(periods=period).iloc[-1] * 100 if len(historical_shifted.dropna()) > period else np.nan
returns = historical_shifted.pct_change() * 100
for window in (7, 14, 30):
    engine_target_feats[f"gold_volatility_{window}"] = returns.tail(window).std() if len(returns.dropna()) >= window else np.nan

# --- What the TRAINING features would be for the SAME boundary date
# Training feature pipeline (create_features.py) uses target.shift(lag) for lags
# and historical_target = target.shift(1) for MA/returns/volatility
# The feature dataset row for date D has:
#   gold_lag_1 = target at D-1
#   gold_ma_3  = mean of target at D-3, D-2, D-1 (via shift(1).rolling(3))
# which is equivalent to looking at last 3 values of target_history (the 3 preceding prices)

# For 2026-09-02, the training-convention "target_features" would be:
training_target_feats = {}
full_series = pd.Series(target_history, dtype="float64")  # ends at 2026-09-01
for lag in (1, 2, 3, 5, 7, 14):
    training_target_feats[f"gold_lag_{lag}"] = full_series.iloc[-lag]
# Training MA: historical_target = target.shift(1)
# For the row that would be 2026-09-02, shift(1) means the row has the price from 2026-09-01
# rolling(3) on historical_target at the 2026-09-02 row = mean of prices at 2026-09-01, 2026-08-31, 2026-08-28
hist_shifted_train = full_series.shift(1)  # index 0..N with [0]=NaN, [N]=full_series[N-1]
# Append one NaN to simulate what training pipeline would see at 2026-09-02 (one step ahead)
extended = pd.concat([full_series, pd.Series([np.nan])], ignore_index=True)
hist_shifted_train_ext = extended.shift(1)
for window in (3, 7, 14, 30):
    training_target_feats[f"gold_ma_{window}"] = hist_shifted_train_ext.iloc[-(window+1):-1].mean()
train_returns = hist_shifted_train_ext.pct_change() * 100
for period in (1, 3, 7):
    training_target_feats[f"gold_return_{period}d"] = hist_shifted_train_ext.pct_change(periods=period).iloc[-1] * 100
for window in (7, 14, 30):
    training_target_feats[f"gold_volatility_{window}"] = train_returns.iloc[-(window+1):-1].std()

print("\n  TARGET FEATURE COMPARISON (Engine vs Training convention):")
print(f"  {'Feature':<25} {'Engine Value':>20} {'Training Conv.':>20} {'Match?':>8}")
print("  " + "-" * 77)
all_target_feat_keys = sorted(set(list(engine_target_feats.keys()) + list(training_target_feats.keys())))
for k in all_target_feat_keys:
    ev = engine_target_feats.get(k, float('nan'))
    tv = training_target_feats.get(k, float('nan'))
    match = "YES" if abs(ev - tv) < 1.0 else "NO  ←←←"
    print(f"  {k:<25} {ev:>20.4f} {tv:>20.4f} {match:>8}")

# ── 5. Market features for 2026-09-02 ────────────────────────────────────────
print("\n[5] Market inputs for 2026-09-02...")
gold_fc_first = float(future_market[future_market["date"] == FORECAST_START]["gold_usd_close_forecast"].iloc[0])
fx_fc_first   = float(future_market[future_market["date"] == FORECAST_START]["usdinr_close_forecast"].iloc[0])

latest_gold_actual = float(market_hist["gold_usd_close"].dropna().iloc[-1])
latest_fx_actual   = float(market_hist["usdinr_close"].dropna().iloc[-1])
latest_gold_date   = market_hist.loc[market_hist["gold_usd_close"].notna(), "date"].max()
latest_fx_date     = market_hist.loc[market_hist["usdinr_close"].notna(), "date"].max()

print(f"  Latest actual gold_usd_close ({latest_gold_date.date()}): {latest_gold_actual:.4f}")
print(f"  Forecast gold_usd_close for 2026-09-02:                  {gold_fc_first:.4f}")
print(f"  Gold USD transition:  {gold_fc_first - latest_gold_actual:+.4f} ({((gold_fc_first-latest_gold_actual)/latest_gold_actual*100):+.4f}%)")
print()
print(f"  Latest actual usdinr_close ({latest_fx_date.date()}):     {latest_fx_actual:.4f}")
print(f"  Forecast usdinr_close for 2026-09-02:                    {fx_fc_first:.4f}")
print(f"  USDINR transition:    {fx_fc_first - latest_fx_actual:+.4f} ({((fx_fc_first-latest_fx_actual)/latest_fx_actual*100):+.4f}%)")
print()
print(f"  gold_inr_proxy actual (latest):  {latest_gold_actual * latest_fx_actual:,.4f}")
print(f"  gold_inr_proxy forecast (09-02): {gold_fc_first * fx_fc_first:,.4f}")
print(f"  Proxy transition:  {(gold_fc_first*fx_fc_first)-(latest_gold_actual*latest_fx_actual):+,.4f} ({((gold_fc_first*fx_fc_first - latest_gold_actual*latest_fx_actual)/(latest_gold_actual*latest_fx_actual)*100):+.4f}%)")

# ── 6. Full feature reproduction for 2026-09-02 ──────────────────────────────
print("\n[6] Reproducing full feature vector for 2026-09-02...")

gold_series = pd.Series([*gold_history, gold_fc_first], dtype="float64")
fx_series   = pd.Series([*fx_history, fx_fc_first], dtype="float64")

market_feats = {
    "gold_usd_open":  np.nan,
    "gold_usd_high":  np.nan,
    "gold_usd_low":   np.nan,
    "gold_usd_close": gold_fc_first,
    "gold_usd_volume": np.nan,
    "usdinr_open":  np.nan,
    "usdinr_high":  np.nan,
    "usdinr_low":   np.nan,
    "usdinr_close": fx_fc_first,
    "gold_inr_proxy": gold_fc_first * fx_fc_first,
}
for period in (1, 3, 7):
    market_feats[f"gold_usd_return_{period}d"] = gold_series.pct_change(periods=period).iloc[-1] * 100 if len(gold_series) > period else np.nan
    market_feats[f"usdinr_return_{period}d"]   = fx_series.pct_change(periods=period).iloc[-1] * 100 if len(fx_series) > period else np.nan
for window in (7, 14):
    market_feats[f"gold_usd_volatility_{window}"] = gold_series.pct_change().tail(window).std() * 100
    market_feats[f"usdinr_volatility_{window}"]   = fx_series.pct_change().tail(window).std() * 100

full_row = {**calendar_feats, **engine_target_feats, **market_feats}
row_frame = pd.DataFrame([full_row], columns=MODEL_FEATURES)
print(f"  Feature vector built: {len(full_row)} features")
print(f"  NaN features: {row_frame.isna().sum().sum()}")

# ── 7. Transform and predict ─────────────────────────────────────────────────
print("\n[7] Transforming and predicting...")
expected_names = list(preprocessor.get_feature_names_out())
transformed = pd.DataFrame(preprocessor.transform(row_frame), columns=expected_names)
reproduced_prediction = float(model.predict(transformed)[0])
print(f"  Reproduced prediction: INR {reproduced_prediction:,.4f}")
print(f"  Stored prediction:     INR {first_fc_price:,.4f}")
match_diff = abs(reproduced_prediction - first_fc_price)
print(f"  Difference:            INR {match_diff:,.6f}")
REPRODUCTION_MATCHED = match_diff < 1.0
print(f"  REPRODUCTION: {'MATCHED ✓' if REPRODUCTION_MATCHED else 'NOT MATCHED ✗ — CRITICAL!'}")

# ── 8. Model coefficient contribution analysis ────────────────────────────────
print("\n[8] Model coefficient contribution analysis...")
coef = model.coef_
intercept = model.intercept_
transformed_values = transformed.values[0]
contributions = coef * transformed_values
total_pred = intercept + contributions.sum()

contrib_df = pd.DataFrame({
    "feature": expected_names,
    "coefficient": coef,
    "transformed_value": transformed_values,
    "contribution": contributions,
})
contrib_df["abs_contribution"] = contrib_df["contribution"].abs()
contrib_df = contrib_df.sort_values("abs_contribution", ascending=False).reset_index(drop=True)

print(f"  Intercept:  {intercept:,.4f}")
print(f"  Sum of contributions: {contributions.sum():,.4f}")
print(f"  Total (intercept + contributions): {total_pred:,.4f}")
print(f"\n  Top 15 contributors (absolute):")
print(f"  {'Feature':<30} {'Coeff':>14} {'Trans.Val':>14} {'Contribution':>14}")
print("  " + "-" * 76)
for _, r in contrib_df.head(15).iterrows():
    sign = "+" if r["contribution"] >= 0 else ""
    print(f"  {r['feature']:<30} {r['coefficient']:>14.4f} {r['transformed_value']:>14.4f} {sign}{r['contribution']:>13.2f}")

# ── 9. Target scale check ─────────────────────────────────────────────────────
print("\n[9] Target scale check...")
y_train = pd.read_csv(PROJECT_ROOT / "data/processed/model_data/y_train.csv")
y_val   = pd.read_csv(PROJECT_ROOT / "data/processed/model_data/y_validation.csv")
y_test  = pd.read_csv(PROJECT_ROOT / "data/processed/model_data/y_test.csv")
print(f"  y_train range: {float(y_train.iloc[:,0].min()):,.0f} — {float(y_train.iloc[:,0].max()):,.0f}")
print(f"  y_val   range: {float(y_val.iloc[:,0].min()):,.0f} — {float(y_val.iloc[:,0].max()):,.0f}")
print(f"  y_test  range: {float(y_test.iloc[:,0].min()):,.0f} — {float(y_test.iloc[:,0].max()):,.0f}")
print(f"  Forecast range: {stored_forecast['forecast_gold_999'].min():,.0f} — {stored_forecast['forecast_gold_999'].max():,.0f}")
print(f"  Actual latest: {latest_actual_price:,.0f}")
scale_ok = (70000 < latest_actual_price < 200000) and (70000 < first_fc_price < 200000)
print(f"  TARGET SCALE CHECK: {'PASSED' if scale_ok else 'FAILED — UNIT MISMATCH SUSPECTED'}")

# ── 10. Off-by-one specific check ─────────────────────────────────────────────
print("\n[10] Off-by-one analysis...")
# In create_features.py: gold_lag_1 = target.shift(1) → for row N, value is target[N-1]
# In the engine: gold_lag_1 = series.iloc[-1] (series = target_history ending at 2026-09-01)
lag1_engine   = engine_target_feats["gold_lag_1"]
lag1_training = historical.loc[historical["date"] == LATEST_TARGET_DATE, "gold_lag_1"].iloc[0]
print(f"  gold_lag_1 in engine for 2026-09-02:          {lag1_engine:,.4f}")
print(f"  gold_lag_1 in feature dataset at 2026-09-01:  {lag1_training:,.4f}")
print(f"  Expected lag1 for 2026-09-02 = price at 2026-09-01: {latest_actual_price:,.4f}")
lag1_correct = abs(lag1_engine - latest_actual_price) < 1.0
print(f"  lag1 == latest actual? {'YES ✓' if lag1_correct else 'NO ✗ OFF-BY-ONE FOUND'}")

# MA check
ma3_engine = engine_target_feats["gold_ma_3"]
# The engine uses: historical = series.shift(1), then historical.tail(3).mean()
# series ends at 2026-09-01, so shift(1) gives [NaN, target[0], ..., target[-2]]
# historical.tail(3) = [target[-3], target[-2], target[-1 shifted]] = prices at 2026-08-28, 2026-08-31, [2026-08-28 again? no...]
# Let's compute manually
# series = [..., P(Aug28), P(Aug31), P(Sep01)]  ← indices N-3, N-2, N-1
# historical = series.shift(1) = [..., P(Aug27), P(Aug28), P(Aug31)]  ← indices N-3, N-2, N-1
# historical.tail(3) = [P(Aug27), P(Aug28), P(Aug31)]   ← MISSING P(Sep01)!
price_sep01 = float(historical[historical["date"] == pd.Timestamp("2026-09-01")]["target_gold_999"].iloc[0])
price_aug31 = float(historical[historical["date"] == pd.Timestamp("2026-08-31")]["target_gold_999"].iloc[0])
price_aug28 = float(historical[historical["date"] == pd.Timestamp("2026-08-28")]["target_gold_999"].iloc[0])
price_aug27 = float(historical[historical["date"] == pd.Timestamp("2026-08-27")]["target_gold_999"].iloc[0])

expected_ma3_correct = (price_sep01 + price_aug31 + price_aug28) / 3
expected_ma3_engine  = (price_aug31 + price_aug28 + price_aug27) / 3   # engine excludes sep01

print(f"\n  gold_ma_3 in engine for 2026-09-02: {ma3_engine:,.4f}")
print(f"  If ma3 used [Sep01, Aug31, Aug28]:  {expected_ma3_correct:,.4f}  (correct boundary convention)")
print(f"  If ma3 used [Aug31, Aug28, Aug27]:  {expected_ma3_engine:,.4f}  (engine double-shift)")
print(f"  Match to engine value:  {'engine double-shift ✓' if abs(ma3_engine - expected_ma3_engine) < 1.0 else 'NEITHER — investigate further'}")
print(f"  Match to correct value: {'correct boundary ✓' if abs(ma3_engine - expected_ma3_correct) < 1.0 else 'NOT matching correct'}")

# The key question: what does the TRAINING data see for the 2026-09-01 row?
# In create_features: historical_target = target.shift(1)
# gold_ma_3 at row 2026-09-01 = historical_target.rolling(3).mean() at that row
#   = mean of historical_target at rows 2026-09-01, 2026-08-31, 2026-08-28
#   = mean of [target.shift(1)[Sep01], target.shift(1)[Aug31], target.shift(1)[Aug28]]
#   = mean of [Aug31, Aug28, Aug27]
ma3_train_at_sep01 = float(historical[historical["date"] == pd.Timestamp("2026-09-01")]["gold_ma_3"].iloc[0])
print(f"\n  gold_ma_3 in training feature dataset at 2026-09-01 row: {ma3_train_at_sep01:,.4f}")
print(f"  Engine gold_ma_3 for 2026-09-02:                         {ma3_engine:,.4f}")
print(f"  These match: {'YES ✓ — engine is consistent with training' if abs(ma3_engine - ma3_train_at_sep01) < 1.0 else 'NO — inconsistency found'}")

# ── 11. Frozen forecast verification ──────────────────────────────────────────
print("\n[11] Verifying frozen forecast integrity...")
print(f"  diwali_reference_estimate: {frozen['diwali_reference_estimate']:,.4f}")
print(f"  lower_estimate:            {frozen['lower_estimate']:,.4f}")
print(f"  upper_estimate:            {frozen['upper_estimate']:,.4f}")
print(f"  future_actual_ibja_used:   {frozen['future_actual_ibja_used']}")
print(f"  test_retraining:           {frozen['test_retraining']}")
FROZEN_OK = (abs(frozen['diwali_reference_estimate'] - 142442.40) < 1.0)
print(f"  FROZEN FORECAST: {'UNCHANGED ✓' if FROZEN_OK else 'CHANGED — CRITICAL!'}")

# ── 12. Save feature snapshot ──────────────────────────────────────────────────
print("\n[12] Saving feature snapshot...")
snapshot = pd.DataFrame([
    {"feature_name": k, "feature_value": full_row.get(k, np.nan)}
    for k in MODEL_FEATURES
])
snapshot.to_csv(REPORTS_DIR / "step40_first_forecast_feature_snapshot.csv", index=False)
print(f"  Saved: reports/step40_first_forecast_feature_snapshot.csv ({len(snapshot)} rows)")

# ── 13. Save contribution report ──────────────────────────────────────────────
print("\n[13] Saving contribution report...")
contrib_out = contrib_df[["feature", "coefficient", "transformed_value", "contribution"]].copy()
contrib_out.to_csv(REPORTS_DIR / "step40_first_forecast_contributions.csv", index=False)
print(f"  Saved: reports/step40_first_forecast_contributions.csv ({len(contrib_out)} rows)")

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Latest actual date:        {LATEST_TARGET_DATE.date()}")
print(f"Latest actual price:       INR {latest_actual_price:,.4f}")
print(f"First forecast date:       {FORECAST_START.date()}")
print(f"First forecast price:      INR {first_fc_price:,.4f}")
print(f"Continuity gap:            INR {gap_abs:,.4f}")
print(f"Continuity percentage:     {gap_pct:.6f}%")
print(f"Direction:                 {'DOWN' if gap_abs < 0 else 'UP'}")
print(f"Reproduction matched:      {'YES' if REPRODUCTION_MATCHED else 'NO'}")
print(f"Target scale:              {'PASS' if scale_ok else 'FAIL'}")
print(f"lag1 correct (=Sep01):     {'PASS' if lag1_correct else 'FAIL'}")
print(f"MA3 consistent w/ training: {'PASS' if abs(ma3_engine - ma3_train_at_sep01) < 1.0 else 'FAIL'}")
print(f"Frozen forecast:           {'UNCHANGED' if FROZEN_OK else 'CHANGED!'}")

print("\nKey findings for root cause:")
print(f"  gold_lag_1 for 2026-09-02 = {lag1_engine:,.2f} == Sep01 price {latest_actual_price:,.2f}: {'YES' if lag1_correct else 'NO'}")
print(f"  Engine MA window is consistent with training MA window: {'YES' if abs(ma3_engine - ma3_train_at_sep01) < 1.0 else 'NO'}")
print(f"  Gold USD transition: {((gold_fc_first-latest_gold_actual)/latest_gold_actual*100):+.3f}%")
print(f"  USDINR transition:   {((fx_fc_first-latest_fx_actual)/latest_fx_actual*100):+.3f}%")
print(f"  gold_inr_proxy drop: {(gold_fc_first*fx_fc_first - latest_gold_actual*latest_fx_actual):+,.2f}")
print("\nDone.")
