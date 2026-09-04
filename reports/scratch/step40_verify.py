import io
import sys
import json
import joblib

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

ROOT = Path('.')
print("=== FROZEN ARTIFACT INTEGRITY CHECK ===")
for path in [
    'models/linear_regression.joblib',
    'models/final_diwali_forecast.json',
    'data/processed/model_data/preprocessor.joblib',
]:
    p = ROOT / path
    print(f"EXISTS={p.exists()}  SIZE={p.stat().st_size:,} bytes  {path}")

frozen = json.loads((ROOT / 'models/final_diwali_forecast.json').read_text(encoding='utf-8'))
ref = frozen['diwali_reference_estimate']
lo  = frozen['lower_estimate']
hi  = frozen['upper_estimate']
print(f"\ndiwali_reference_estimate: {ref:,.4f}")
print(f"lower_estimate:            {lo:,.4f}")
print(f"upper_estimate:            {hi:,.4f}")
print(f"future_actual_ibja_used:   {frozen['future_actual_ibja_used']}")
print(f"test_retraining:           {frozen['test_retraining']}")
ok = abs(ref - 142442.40) < 1.0
print(f"\nFROZEN FORECAST: {'UNCHANGED' if ok else 'MODIFIED!'}")

print("\n=== OUTPUT FILES CREATED ===")
for path in [
    'reports/step40_forecast_continuity_diagnostic.md',
    'reports/step40_first_forecast_feature_snapshot.csv',
    'reports/step40_first_forecast_contributions.csv',
]:
    p = ROOT / path
    print(f"EXISTS={p.exists()}  SIZE={p.stat().st_size:,} bytes  {path}")
