"""Tests for Step 43 What-If sensitivity analysis artifacts."""

from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SENSITIVITY_CSV = PROJECT_ROOT / "reports" / "diwali_sensitivity_analysis.csv"


def test_sensitivity_analysis_csv_structure():
    """Verify diwali_sensitivity_analysis.csv has 5 predefined scenarios and correct baseline."""
    assert SENSITIVITY_CSV.exists(), f"File missing: {SENSITIVITY_CSV}"
    df = pd.read_csv(SENSITIVITY_CSV)
    assert len(df) == 5, f"Expected exactly 5 scenario rows, got {len(df)}"

    required_cols = ["scenario", "gold_market_adjustment", "usdinr_adjustment", "diwali_reference_estimate"]
    for col in required_cols:
        assert col in df.columns, f"Column '{col}' missing from sensitivity CSV"

    # Numeric estimates
    estimates = pd.to_numeric(df["diwali_reference_estimate"], errors="coerce")
    assert not estimates.isna().any(), "Sensitivity estimates contain non-numeric values"
    assert (estimates > 0).all(), "Sensitivity estimates contain non-positive values"

    # Check baseline row
    baseline_row = df[df["scenario"].str.lower().str.contains("baseline")]
    assert not baseline_row.empty, "Baseline scenario row not found in sensitivity CSV"
    base_pred = float(baseline_row.iloc[0]["diwali_reference_estimate"])
    assert abs(base_pred - 142442.407) < 1.0, f"Unexpected baseline estimate: {base_pred}"
