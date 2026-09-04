"""Tests for FastAPI backend endpoints using TestClient."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from api.main import app, read_json_artifact, PROJECT_ROOT as API_ROOT
from fastapi import HTTPException

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "gold-price-intelligence-api"


def test_readiness_endpoint_healthy():
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert "linear_regression.joblib" in data["checks"]
    assert data["checks"]["linear_regression.joblib"] == "AVAILABLE"
    assert data["checks"]["final_diwali_forecast.json"] == "AVAILABLE"


def test_readiness_endpoint_missing_artifact(monkeypatch):
    from api import main
    fake_artifacts = main.REQUIRED_READINESS_ARTIFACTS + [main.PROJECT_ROOT / "models" / "missing_file_test.joblib"]
    monkeypatch.setattr(main, "REQUIRED_READINESS_ARTIFACTS", fake_artifacts)
    res = client.get("/ready")
    assert res.status_code == 503
    data = res.json()
    assert "Service not ready" in data["detail"]


def test_cors_headers():
    res = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_model_info_endpoint():
    res = client.get("/api/model-info")
    assert res.status_code == 200
    data = res.json()
    assert data["model"] == "Linear Regression"
    assert data["feature_count"] == 46
    assert abs(data["test"]["MAE"] - 2122.606) < 1.0


def test_model_comparison_endpoint():
    res = client.get("/api/model-comparison")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 4, f"Expected 4 models in comparison, got {len(data)}"
    selected_count = sum(1 for m in data if m.get("selected"))
    assert selected_count == 1, "Exactly one model must be marked selected"


def test_diwali_prediction_endpoint():
    res = client.get("/api/diwali-prediction")
    assert res.status_code == 200
    data = res.json()
    assert data["diwali_date"] == "2026-11-08"
    assert abs(data["diwali_reference_estimate"]["forecast"] - 142442.407) < 1.0
    assert data["estimated_range"]["lower"] < data["diwali_reference_estimate"]["forecast"] < data["estimated_range"]["upper"]


def test_forecast_endpoint():
    res = client.get("/api/forecast")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_historical_data_endpoint():
    res = client.get("/api/historical-data")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_prediction_drivers_endpoint():
    res = client.get("/api/prediction-drivers")
    assert res.status_code == 200
    data = res.json()
    assert data["model"] == "Linear Regression"
    assert data["forecast_date"] == "2026-11-08"
    assert data["reconstruction_status"] == "PASS"
    assert len(data["top_positive_drivers"]) == 5
    assert len(data["top_negative_drivers"]) == 5


def test_what_if_endpoint():
    res = client.get("/api/what-if")
    assert res.status_code == 200
    data = res.json()
    assert abs(data["baseline_prediction"] - 142442.407) < 1.0
    assert len(data["scenarios"]) == 5


def test_missing_artifact_error_handling():
    """Verify missing artifact raises HTTP 500 cleanly without leaking internal stack traces."""
    fake_path = API_ROOT / "non_existent_artifact_xyz.json"
    with pytest.raises(HTTPException) as exc_info:
        read_json_artifact(fake_path)
    assert exc_info.value.status_code == 500
    assert "Required artifact is missing" in exc_info.value.detail

