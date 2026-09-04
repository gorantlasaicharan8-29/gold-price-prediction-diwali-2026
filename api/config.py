"""Production environment configuration for Gold Price Intelligence API."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv(dotenv_path: Path) -> None:
    """Load key=value pairs from a local .env file into os.environ if present."""
    if dotenv_path.exists() and dotenv_path.is_file():
        for line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv(PROJECT_ROOT / ".env")

# Environment variables with local development defaults
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
API_TITLE = "Gold Price Intelligence API"
API_VERSION = "1.0.0"
API_DESCRIPTION = (
    "Production API for the Gold Price Prediction System during Diwali 2026. "
    "Provides read-only access to IBJA Gold 999 forecasts, model metrics, "
    "prediction driver explainability, and What-If scenario sensitivity analysis."
)

DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]


def get_cors_origins() -> list[str]:
    """Parse allowed CORS origins from environment variable or return safe local defaults."""
    env_origins = os.getenv("CORS_ORIGINS")
    if not env_origins:
        return DEFAULT_CORS_ORIGINS

    origins = [origin.strip() for origin in env_origins.split(",") if origin.strip()]
    return origins if origins else DEFAULT_CORS_ORIGINS

