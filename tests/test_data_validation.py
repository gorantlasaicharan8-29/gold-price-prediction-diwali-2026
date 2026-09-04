"""Tests for raw IBJA target data validation."""

from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_IBJA_PATH = PROJECT_ROOT / "data" / "raw" / "ibja_gold_999_2025_2026.csv"


def test_raw_ibja_file_exists():
    """Verify raw IBJA target file exists and is readable."""
    assert RAW_IBJA_PATH.exists(), f"Raw IBJA dataset not found at {RAW_IBJA_PATH}"
    assert RAW_IBJA_PATH.stat().st_size > 0, "Raw IBJA dataset file is empty"


def test_raw_ibja_structure_and_types():
    """Verify required columns, date validity, and numeric targets."""
    df = pd.read_csv(RAW_IBJA_PATH)
    assert not df.empty, "Raw IBJA dataset contains zero rows"
    assert "date" in df.columns, "date column missing from raw IBJA dataset"

    # Date parsing & chronological ordering
    parsed_dates = pd.to_datetime(df["date"], errors="coerce")
    assert not parsed_dates.isna().any(), "Raw IBJA dataset contains invalid date entries"
    assert parsed_dates.is_monotonic_increasing, "Raw IBJA dates are not chronologically sorted"
    assert df["date"].duplicated().sum() == 0, "Raw IBJA dataset contains duplicate dates"

    # Target column validation (gold_999_avg or target_gold_999)
    target_col = "target_gold_999" if "target_gold_999" in df.columns else "gold_999_avg"
    assert target_col in df.columns or "gold_999_average" in df.columns, "No valid target column found"

    actual_col = target_col if target_col in df.columns else "gold_999_average"
    numeric_targets = pd.to_numeric(df[actual_col], errors="coerce")
    assert not numeric_targets.isna().any(), f"Target column '{actual_col}' contains missing/non-numeric values"
    assert (numeric_targets > 0).all(), f"Target column '{actual_col}' contains non-positive values"
