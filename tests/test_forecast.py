"""Tests for frozen Diwali 2026 forecast artifacts and recursive series integrity."""

import json
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FINAL_FORECAST_JSON = PROJECT_ROOT / "models" / "final_diwali_forecast.json"
RECURSIVE_CSV = PROJECT_ROOT / "data" / "processed" / "model_data" / "diwali_recursive_forecast.csv"
DIAGNOSTIC_TXT = PROJECT_ROOT / "reports" / "diwali_forecast_diagnostic_report.txt"


def test_frozen_diwali_forecast_json():
    """Verify final_diwali_forecast.json parameters and range ordering."""
    assert FINAL_FORECAST_JSON.exists(), f"File missing: {FINAL_FORECAST_JSON}"
    fc = json.loads(FINAL_FORECAST_JSON.read_text(encoding="utf-8"))

    assert fc["selected_model"] == "Linear Regression"
    assert fc["diwali_date"] == "2026-11-08"
    assert fc["previous_business_day"] == "2026-11-06"
    assert fc["next_business_day"] == "2026-11-09"

    ref = fc["diwali_reference_estimate"]
    low = fc["lower_estimate"]
    high = fc["upper_estimate"]

    # Target values check
    assert abs(ref - 142442.407) < 1.0, f"Unexpected reference estimate: {ref}"
    assert abs(low - 137889.898) < 1.0, f"Unexpected lower estimate: {low}"
    assert abs(high - 144859.721) < 1.0, f"Unexpected upper estimate: {high}"

    # Range ordering invariant
    assert low < ref < high, f"Forecast range invariant broken: low={low}, ref={ref}, high={high}"


def test_recursive_forecast_csv():
    """Verify diwali_recursive_forecast.csv contains valid business-day predictions."""
    assert RECURSIVE_CSV.exists(), f"File missing: {RECURSIVE_CSV}"
    df = pd.read_csv(RECURSIVE_CSV)
    assert not df.empty, "Recursive forecast CSV is empty"
    assert "date" in df.columns
    assert "forecast_gold_999" in df.columns

    # Date validity & non-duplication
    dates = pd.to_datetime(df["date"], errors="coerce")
    assert not dates.isna().any(), "Recursive forecast contains invalid dates"
    assert df["date"].duplicated().sum() == 0, "Recursive forecast contains duplicate dates"
    assert dates.is_monotonic_increasing, "Recursive forecast dates are not chronological"

    # Value validity
    preds = pd.to_numeric(df["forecast_gold_999"], errors="coerce")
    assert not preds.isna().any(), "Recursive forecast contains NaNs or non-numeric values"
    assert (preds > 0).all(), "Recursive forecast contains non-positive predictions"


def test_forecast_continuity_diagnostic_documented():
    """Verify documented continuity diagnostic report exists."""
    assert DIAGNOSTIC_TXT.exists(), f"File missing: {DIAGNOSTIC_TXT}"
    content = DIAGNOSTIC_TXT.read_text(encoding="utf-8")
    assert "DIWALI FORECAST DIAGNOSTIC REPORT" in content
    assert "Latest actual IBJA price: 153,990" in content or "153,990" in content
    assert "First recursive forecast: 141,292" in content or "141,292" in content
