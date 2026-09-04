"""Tests for master dataset and engineered feature dataset integrity."""

from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MASTER_PATH = PROJECT_ROOT / "data" / "processed" / "gold_master_dataset.csv"
FEATURE_PATH = PROJECT_ROOT / "data" / "processed" / "gold_feature_dataset.csv"

EXCLUDED_TARGET_SOURCES = ["gold_999_am", "gold_999_pm", "gold_999_avg", "gold_999_average"]


def test_master_dataset_integrity():
    """Verify gold_master_dataset.csv exists, has valid target and no missing values."""
    assert MASTER_PATH.exists(), f"Master dataset not found at {MASTER_PATH}"
    df = pd.read_csv(MASTER_PATH)
    assert not df.empty, "Master dataset is empty"
    assert "date" in df.columns, "date column missing from master dataset"
    assert "target_gold_999" in df.columns, "target_gold_999 missing from master dataset"

    # Date validity
    dates = pd.to_datetime(df["date"], errors="coerce")
    assert not dates.isna().any(), "Master dataset contains invalid dates"
    assert df["date"].duplicated().sum() == 0, "Master dataset contains duplicate dates"
    assert dates.is_monotonic_increasing, "Master dataset dates are not chronologically sorted"

    # Target values
    targets = pd.to_numeric(df["target_gold_999"], errors="coerce")
    assert not targets.isna().any(), "Master dataset target_gold_999 contains missing values"
    assert (targets > 0).all(), "Master dataset target_gold_999 contains non-positive values"


def test_feature_dataset_integrity_and_leakage_protection():
    """Verify gold_feature_dataset.csv has 46 predictor features and no same-day target source leakage."""
    assert FEATURE_PATH.exists(), f"Feature dataset not found at {FEATURE_PATH}"
    df = pd.read_csv(FEATURE_PATH)
    assert not df.empty, "Feature dataset is empty"
    assert "target_gold_999" in df.columns, "target_gold_999 missing from feature dataset"

    # Date checks
    dates = pd.to_datetime(df["date"], errors="coerce")
    assert not dates.isna().any(), "Feature dataset contains invalid dates"
    assert df["date"].duplicated().sum() == 0, "Feature dataset contains duplicate dates"
    assert dates.is_monotonic_increasing, "Feature dataset dates are not chronologically sorted"

    # Target checks
    targets = pd.to_numeric(df["target_gold_999"], errors="coerce")
    assert not targets.isna().any(), "Feature dataset target_gold_999 contains missing values"

    # Predictor columns check
    non_predictor = ["date", "target_gold_999", "source", *EXCLUDED_TARGET_SOURCES]
    predictor_cols = [c for c in df.columns if c not in non_predictor]
    assert len(predictor_cols) == 46, f"Expected 46 predictor columns, found {len(predictor_cols)}"

    # Leakage check: confirm same-day target sources are not present in predictor_cols
    for source_col in EXCLUDED_TARGET_SOURCES:
        assert source_col not in predictor_cols, f"Data leakage detected: {source_col} present in predictor features"
