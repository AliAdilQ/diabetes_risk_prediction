"""Public pages, error handling, and secure initialization behavior."""

from pathlib import Path

import pytest

from app.features import DISCLAIMER
from config import configuration


@pytest.mark.parametrize("path", ["/", "/predict", "/about", "/model-info", "/admin/login"])
def test_public_pages(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert DISCLAIMER in response.text
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]


@pytest.mark.parametrize("path, status", [("/does-not-exist", 404), ("/test-forbidden", 403)])
def test_custom_error_pages(client, path, status):
    response = client.get(path)
    assert response.status_code == status
    assert f'class="error-code">{status}' in response.text


def test_500_page(app, client):
    app.config["PROPAGATE_EXCEPTIONS"] = False
    response = client.get("/test-server-error")
    assert response.status_code == 500
    assert "Something interrupted the flow" in response.text


def test_missing_model_and_metrics(app, client, tmp_path, valid_inputs):
    app.config["MODEL_PATH"] = tmp_path / "missing.pkl"
    app.config["METRICS_PATH"] = tmp_path / "missing.json"
    response = client.get("/predict")
    assert response.status_code == 200
    assert "Model unavailable" in response.text
    assert client.post("/predict", data=valid_inputs).status_code == 503
    assert "ready to be trained" in client.get("/model-info").text
    assert client.post("/api/predict", json=valid_inputs).status_code == 503


def test_production_rejects_weak_secret(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "change-me")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        configuration()


def test_production_secure_cookies(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "a" * 64)
    config = configuration()
    assert config["SESSION_COOKIE_SECURE"]
    assert config["SESSION_COOKIE_HTTPONLY"]
    assert config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert not config["AUTO_CREATE_DB"]


def test_readme_screenshots_exist():
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    for name in ["home", "prediction", "result", "admin-login", "admin-dashboard"]:
        path = root / "screenshots" / f"{name}.png"
        assert f"screenshots/{name}.png" in readme
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
