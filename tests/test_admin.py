"""Authentication, record management, empty analytics, and demo seed behavior."""

import pytest

from app import create_app
from app.extensions import db
from app.models import Admin, Prediction
from scripts.seed_database import seed_demo


@pytest.mark.parametrize("path", ["/admin", "/admin/predictions", "/admin/model-performance",
                                  "/admin/predictions/1", "/admin/predictions/export"])
def test_unauthorized_admin_redirect(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert "/admin/login" in response.location


def test_invalid_login(client):
    response = client.post("/admin/login", data={"username": "admin", "password": "wrong"})
    assert response.status_code == 401
    assert "Username or password is incorrect" in response.text
    assert client.get("/admin").status_code == 302


def test_password_is_hashed(app):
    with app.app_context():
        user = db.session.scalar(db.select(Admin))
        assert user.password_hash != "Admin@123"
        assert user.check_password("Admin@123")
        assert not user.check_password("wrong")


def test_login_empty_dashboard_and_logout(authenticated_client):
    response = authenticated_client.get("/admin")
    assert response.status_code == 200
    assert "Dashboard overview" in response.text
    assert "No predictions here yet" in response.text
    assert authenticated_client.get("/admin/logout").status_code == 405
    assert authenticated_client.post("/admin/logout").status_code == 302
    assert authenticated_client.get("/admin").status_code == 302


@pytest.mark.parametrize("destination", ["https://example.com", "//example.com", "/\\example.com", "/predict"])
def test_login_prevents_open_redirect(client, destination):
    response = client.post("/admin/login", query_string={"next": destination},
                           data={"username": "admin", "password": "Admin@123"})
    assert response.location.rstrip("/") == "/admin"


def test_seed_idempotence_and_populated_analytics(app, authenticated_client):
    assert seed_demo(app) == 24
    assert seed_demo(app) == 0
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Admin.id))) == 1
        assert db.session.scalar(db.select(db.func.count(Prediction.id))) == 24
        classes = set(db.session.scalars(db.select(Prediction.prediction)).all())
        assert classes == {0, 1}
    assert authenticated_client.get("/admin").status_code == 200
    assert authenticated_client.get("/admin/model-performance").status_code == 200


def test_filter_pagination_detail_delete_export(app, authenticated_client):
    seed_demo(app)
    response = authenticated_client.get("/admin/predictions?page=2")
    assert response.status_code == 200
    assert "13–24 of 24" in response.text
    high = authenticated_client.get("/admin/predictions?risk=1&sort=probability")
    assert high.status_code == 200
    assert 'class="pill risk-low"' not in high.text
    csv = authenticated_client.get("/admin/predictions/export?risk=1")
    assert csv.status_code == 200
    assert "attachment" in csv.headers["Content-Disposition"]
    assert csv.text.startswith("id,pregnancies,glucose")
    with app.app_context():
        record = db.session.scalar(db.select(Prediction))
        record_id = record.id
    assert authenticated_client.get(f"/admin/predictions/{record_id}").status_code == 200
    assert authenticated_client.get(f"/admin/predictions/{record_id}/delete").status_code == 405
    assert authenticated_client.post(f"/admin/predictions/{record_id}/delete").status_code == 302
    with app.app_context():
        assert db.session.get(Prediction, record_id) is None


def test_search_and_bad_filters(app, authenticated_client):
    seed_demo(app)
    assert authenticated_client.get("/admin/predictions?q=Logistic").status_code == 200
    assert authenticated_client.get("/admin/predictions?q=' OR 1=1 --").status_code == 200
    assert authenticated_client.get("/admin/predictions?from=not-a-date").status_code == 400
    assert authenticated_client.get("/admin/predictions?sort=bad&page=bad").status_code == 200


def test_csrf_enforced_on_admin_actions(app, authenticated_client):
    seed_demo(app)
    app.config["WTF_CSRF_ENABLED"] = True
    assert authenticated_client.post("/admin/logout").status_code == 400
    assert authenticated_client.post("/admin/predictions/1/delete").status_code == 400
    with app.app_context():
        assert db.session.get(Prediction, 1) is not None


def test_production_cannot_seed(app):
    app.config["ENVIRONMENT"] = "production"
    with pytest.raises(RuntimeError, match="disabled in production"):
        seed_demo(app)


def test_login_rate_limit(tmp_path):
    application = create_app({"TESTING": True, "SECRET_KEY": "test-rate-limit-secret",
                              "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "WTF_CSRF_ENABLED": False, "RATELIMIT_ENABLED": True})
    client = application.test_client()
    for _ in range(5):
        assert client.post("/admin/login", data={"username": "nobody", "password": "wrong"}).status_code == 401
    assert client.post("/admin/login", data={"username": "nobody", "password": "wrong"}).status_code == 429


def test_cli_admin_creation_and_password_rotation(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["create-admin", "--username", "reviewer", "--email",
                                "reviewer@example.com", "--password", "a-long-test-password"])
    assert result.exit_code == 0
    result = runner.invoke(args=["change-admin-password", "--username", "reviewer",
                                "--password", "a-new-test-password"])
    assert result.exit_code == 0
    with app.app_context():
        user = db.session.scalar(db.select(Admin).where(Admin.username == "reviewer"))
        assert user.check_password("a-new-test-password")
        assert not user.check_password("a-long-test-password")
