"""Isolated database fixtures; tests never touch the local demo database."""

import pytest
from flask import abort

from app import create_app
from app.extensions import db
from app.features import FEATURES
from app.models import Admin


@pytest.fixture()
def app(tmp_path):
    application = create_app({
        "TESTING": True, "SECRET_KEY": "test-only-secret-with-enough-characters",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        "WTF_CSRF_ENABLED": False, "RATELIMIT_ENABLED": False, "AUTO_CREATE_DB": True,
    })

    @application.get("/test-forbidden")
    def test_forbidden():
        abort(403)

    @application.get("/test-server-error")
    def test_server_error():
        raise RuntimeError("Intentional test error")

    with application.app_context():
        user = Admin(username="admin", email="admin@example.com")
        user.set_password("Admin@123")
        db.session.add(user)
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def valid_inputs():
    return {feature.key: feature.example for feature in FEATURES}


@pytest.fixture()
def authenticated_client(client):
    response = client.post("/admin/login", data={"username": "admin", "password": "Admin@123"})
    assert response.status_code == 302
    return client
