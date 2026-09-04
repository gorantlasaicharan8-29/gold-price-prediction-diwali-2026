"""Tests for model binary artifacts, selection status, and evaluation metrics."""

import json
from pathlib import Path
import joblib
import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "model_data"

MODEL_FILES = {
    "linear_regression": MODELS_DIR / "linear_regression.joblib",
    "random_forest": MODELS_DIR / "random_forest.joblib",
    "gradient_boosting": MODELS_DIR / "gradient_boosting.joblib",
    "xgboost": MODELS_DIR / "xgboost.joblib",
}
PREPROCESSOR_PATH = MODEL_DATA_DIR / "preprocessor.joblib"
BEST_MODEL_TXT = MODELS_DIR / "best_validation_model.txt"
METADATA_JSON = MODELS_DIR / "model_metadata.json"


def test_model_binaries_exist_and_load():
    """Verify all 4 model binaries and preprocessor exist and load cleanly."""
    for name, path in MODEL_FILES.items():
        assert path.exists(), f"Model file missing: {path}"
        model = joblib.load(path)
        assert model is not None, f"Failed to load model from {path}"

    assert PREPROCESSOR_PATH.exists(), f"Preprocessor missing: {PREPROCESSOR_PATH}"
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    assert preprocessor is not None, "Failed to load preprocessor"


def test_linear_regression_coefficients():
    """Verify Linear Regression model exposes valid coef_ and intercept_."""
    lr_model = joblib.load(MODEL_FILES["linear_regression"])
    assert hasattr(lr_model, "coef_"), "Linear Regression missing coef_ attribute"
    assert hasattr(lr_model, "intercept_"), "Linear Regression missing intercept_ attribute"
    assert lr_model.coef_.shape == (46,), f"Expected coef_ shape (46,), got {lr_model.coef_.shape}"
    assert np.isfinite(lr_model.intercept_), "Linear Regression intercept is not finite"


def test_selected_model_is_linear_regression():
    """Verify best_validation_model.txt identifies Linear Regression."""
    assert BEST_MODEL_TXT.exists(), f"File missing: {BEST_MODEL_TXT}"
    content = BEST_MODEL_TXT.read_text(encoding="utf-8").strip()
    assert content == "Linear Regression", f"Expected selected model 'Linear Regression', got '{content}'"


def test_model_metadata_test_metrics():
    """Verify final holdout test metrics match expected performance within tolerance."""
    assert METADATA_JSON.exists(), f"File missing: {METADATA_JSON}"
    meta = json.loads(METADATA_JSON.read_text(encoding="utf-8"))

    assert meta["selected_model"] == "Linear Regression"
    assert meta["feature_count"] == 46
    assert meta["training_rows"] == 117
    assert meta["validation_rows"] == 25
    assert meta["test_rows"] == 26

    # Test metrics tolerances
    assert abs(meta["test_MAE"] - 2122.606) < 1.0, f"Unexpected test MAE: {meta['test_MAE']}"
    assert abs(meta["test_RMSE"] - 2576.559) < 1.0, f"Unexpected test RMSE: {meta['test_RMSE']}"
    assert abs(meta["test_MAPE"] - 1.41778) < 0.05, f"Unexpected test MAPE: {meta['test_MAPE']}"
    assert abs(meta["test_R2"] - 0.84088) < 0.01, f"Unexpected test R2: {meta['test_R2']}"
