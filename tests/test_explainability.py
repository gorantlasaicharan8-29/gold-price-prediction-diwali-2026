"""Tests for Step 42 Explainable AI prediction driver artifacts."""

import json
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DRIVERS_JSON = PROJECT_ROOT / "models" / "prediction_drivers.json"
DRIVERS_CSV = PROJECT_ROOT / "reports" / "step42_prediction_drivers.csv"


def test_prediction_drivers_json_structure():
    """Verify prediction_drivers.json schema and reconstruction status PASS."""
    assert DRIVERS_JSON.exists(), f"File missing: {DRIVERS_JSON}"
    data = json.loads(DRIVERS_JSON.read_text(encoding="utf-8"))

    assert data["model"] == "Linear Regression"
    assert data["forecast_date"] == "2026-11-08"
    assert abs(data["prediction"] - 142442.407) < 1.0
    assert abs(data["intercept"] - (-139595.857)) < 1.0

    status = data.get("reconstruction_status") or data.get("contribution_reconstruction_status")
    assert status == "PASS", f"Expected reconstruction status 'PASS', got '{status}'"

    assert len(data.get("top_positive_drivers", [])) == 5
    assert len(data.get("top_negative_drivers", [])) == 5
    assert len(data.get("positive_drivers", [])) > 0
    assert len(data.get("negative_drivers", [])) > 0


def test_prediction_drivers_csv():
    """Verify step42_prediction_drivers.csv exists and has required numeric columns."""
    assert DRIVERS_CSV.exists(), f"File missing: {DRIVERS_CSV}"
    df = pd.read_csv(DRIVERS_CSV)
    assert not df.empty, "Drivers CSV is empty"

    required_cols = ["feature", "transformed_value", "coefficient", "contribution", "absolute_contribution", "direction"]
    for col in required_cols:
        assert col in df.columns, f"Column '{col}' missing from drivers CSV"

    # Numeric contributions
    contribs = pd.to_numeric(df["contribution"], errors="coerce")
    assert not contribs.isna().any(), "Drivers CSV contains non-numeric contributions"
    assert len(df) == 46, f"Expected 46 feature contribution rows, got {len(df)}"
