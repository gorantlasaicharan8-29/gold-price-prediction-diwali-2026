"""Audit frontend source code for forbidden hard-coded production values."""

from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = PROJECT_ROOT / "frontend" / "src"

# Forbidden exact production numbers that must be fetched dynamically from API
FORBIDDEN_PROD_STRINGS = [
    ("142442.41", "Diwali reference forecast estimate"),
    ("142442.40", "Diwali reference forecast estimate"),
    ("137889.90", "Lower range estimate"),
    ("144859.72", "Upper range estimate"),
    ("2122.61", "Test MAE metric"),
    ("2576.56", "Test RMSE metric"),
    ("141027.81", "What-If scenario prediction"),
    ("143778.68", "What-If scenario prediction"),
    ("144643.05", "What-If scenario prediction"),
    ("140078.57", "What-If scenario prediction"),
    ("109408.82", "Prediction driver contribution value"),
    ("71221.21", "5g weight prediction"),
    ("213663.62", "15g weight prediction"),
]


def test_frontend_source_contains_no_hardcoded_production_values():
    """Verify frontend/src JS/JSX code contains zero hard-coded production numbers."""
    assert FRONTEND_SRC.exists(), f"Frontend source directory missing at {FRONTEND_SRC}"

    src_files = list(FRONTEND_SRC.rglob("*.jsx")) + list(FRONTEND_SRC.rglob("*.js"))
    assert len(src_files) > 0, "No JS/JSX files found in frontend/src"

    violations = []

    for file_path in src_files:
        content = file_path.read_text(encoding="utf-8")
        for forbidden_str, label in FORBIDDEN_PROD_STRINGS:
            if forbidden_str in content:
                rel_path = file_path.relative_to(PROJECT_ROOT)
                violations.append(f"{rel_path}: Hard-coded {label} ('{forbidden_str}')")

    assert not violations, "Hard-coded production values found in frontend source:\n" + "\n".join(violations)
