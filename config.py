"""Environment-based settings; SQLite resolves inside Flask's instance folder."""

import os
import secrets
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def configuration():
    """Fail closed in production and use a random local-only session secret."""
    environment = os.getenv("FLASK_ENV", "development").lower()
    production = environment == "production"
    secret = os.getenv("SECRET_KEY", "")
    weak_secret = len(secret) < 32 or secret.lower() in {"change-me", "secret"}
    if production and weak_secret:
        raise RuntimeError("Production requires a random SECRET_KEY of at least 32 characters.")
    if weak_secret:
        secret = secrets.token_hex(32)
    return {
        "SECRET_KEY": secret,
        "ENVIRONMENT": environment,
        "SQLALCHEMY_DATABASE_URI": os.getenv("DATABASE_URL", "sqlite:///diabetes.db"),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": production,
        "REMEMBER_COOKIE_HTTPONLY": True,
        "REMEMBER_COOKIE_SECURE": production,
        "PERMANENT_SESSION_LIFETIME": timedelta(minutes=30),
        "MAX_CONTENT_LENGTH": 16 * 1024,
        "WTF_CSRF_TIME_LIMIT": 3600,
        "RATELIMIT_STORAGE_URI": os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
        "RATELIMIT_HEADERS_ENABLED": True,
        "AUTO_CREATE_DB": not production,
        "MODEL_PATH": ROOT / "models" / "diabetes_model.pkl",
        "METRICS_PATH": ROOT / "models" / "model_metrics.json",
    }
