"""Tests for FastAPI /api/weight-prediction endpoint."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from api.main import app

client = TestClient(app)


def test_weight_prediction_1g():
    res = client.get("/api/weight-prediction?weight=1")
    assert res.status_code == 200
    data = res.json()
    assert data["weight_grams"] == 1.0
    assert abs(data["predicted_price"] - 14244.24) < 1.0
    assert data["currency"] == "INR"
    assert data["model"] == "Linear Regression"


def test_weight_prediction_5g():
    res = client.get("/api/weight-prediction?weight=5")
    assert res.status_code == 200
    data = res.json()
    assert data["weight_grams"] == 5.0
    assert abs(data["predicted_price"] - 71221.20) < 1.0
    assert abs(data["lower_estimate"] - 68944.95) < 1.0
    assert abs(data["upper_estimate"] - 72429.86) < 1.0


def test_weight_prediction_10g_equals_frozen_forecast():
    res = client.get("/api/weight-prediction?weight=10")
    assert res.status_code == 200
    data = res.json()
    assert data["weight_grams"] == 10.0
    assert abs(data["predicted_price"] - 142442.41) < 1.0
    assert abs(data["lower_estimate"] - 137889.90) < 1.0
    assert abs(data["upper_estimate"] - 144859.72) < 1.0


def test_weight_prediction_15g():
    res = client.get("/api/weight-prediction?weight=15")
    assert res.status_code == 200
    data = res.json()
    assert data["weight_grams"] == 15.0
    assert abs(data["predicted_price"] - 213663.61) < 1.0


def test_weight_prediction_decimal():
    res = client.get("/api/weight-prediction?weight=2.5")
    assert res.status_code == 200
    data = res.json()
    assert data["weight_grams"] == 2.5
    assert abs(data["predicted_price"] - (14244.241 * 2.5)) < 1.0


def test_weight_prediction_calculation_consistency():
    res_1g = client.get("/api/weight-prediction?weight=1").json()
    res_5g = client.get("/api/weight-prediction?weight=5").json()
    res_10g = client.get("/api/weight-prediction?weight=10").json()
    res_15g = client.get("/api/weight-prediction?weight=15").json()

    p1 = res_1g["predicted_price"]
    p5 = res_5g["predicted_price"]
    p10 = res_10g["predicted_price"]
    p15 = res_15g["predicted_price"]

    assert abs(p1 * 10 - p10) < 1.0
    assert abs(p5 * 2 - p10) < 1.0
    assert abs(p1 * 15 - p15) < 1.0


def test_weight_prediction_invalid_bounds():
    # Below min (0)
    res_zero = client.get("/api/weight-prediction?weight=0")
    assert res_zero.status_code in (400, 422)

    # Negative (-2)
    res_neg = client.get("/api/weight-prediction?weight=-2")
    assert res_neg.status_code in (400, 422)

    # Above max (16)
    res_high = client.get("/api/weight-prediction?weight=16")
    assert res_high.status_code in (400, 422)

    # Non-numeric ("abc")
    res_alpha = client.get("/api/weight-prediction?weight=abc")
    assert res_alpha.status_code in (400, 422)
