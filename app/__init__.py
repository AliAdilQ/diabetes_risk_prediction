"""Flask application factory and shared security/error handling."""

from pathlib import Path

import click
from flask import Flask, jsonify, render_template, request
from flask_wtf.csrf import CSRFError

from config import configuration
from .extensions import csrf, db, limiter, login_manager
from .features import DISCLAIMER, FEATURES


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(configuration())
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.login_view = "admin.login"
    login_manager.login_message = "Sign in to access the admin workspace."
    login_manager.login_message_category = "info"
    login_manager.session_protection = "strong"

    from .models import Admin
    from .routes import main
    from .admin_routes import admin

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(Admin, int(user_id))
        except (TypeError, ValueError):
            return None

    app.register_blueprint(main)
    app.register_blueprint(admin)

    @app.context_processor
    def shared_context():
        return {"disclaimer": DISCLAIMER, "features": FEATURES}

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        if app.config["SESSION_COOKIE_SECURE"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        if request.path.startswith(("/admin", "/api", "/prediction-result", "/predict")):
            response.headers["Cache-Control"] = "no-store"
        return response

    def render_error(error):
        code = getattr(error, "code", 500) or 500
        if code == 500:
            db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify(error="Request could not be completed", status=code), code
        return render_template("errors/error.html", code=code), code

    for code in (400, 403, 404, 405, 413, 429, 500, 503):
        app.register_error_handler(code, render_error)

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        if request.path.startswith("/api/"):
            return jsonify(error="A valid CSRF token is required. Fetch /api/csrf-token first."), 400
        return render_template("errors/error.html", code=400,
                               message="Your form expired. Refresh the page and try again."), 400

    @app.cli.command("init-db")
    def init_db():
        """Create database tables without installing any demo credentials."""
        db.create_all()
        click.echo("Database tables initialized.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--email", prompt=True)
    @click.password_option()
    def create_admin(username, email, password):
        """Create a unique administrator using an interactive password prompt."""
        if len(password) < 12:
            raise click.ClickException("Use a password of at least 12 characters.")
        if db.session.scalar(db.select(Admin).where(Admin.username == username)):
            raise click.ClickException("That username already exists.")
        if db.session.scalar(db.select(Admin).where(Admin.email == email)):
            raise click.ClickException("That email already exists.")
        user = Admin(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Administrator created.")

    @app.cli.command("change-admin-password")
    @click.option("--username", prompt=True)
    @click.password_option()
    def change_admin_password(username, password):
        """Rotate an existing administrator's password."""
        user = db.session.scalar(db.select(Admin).where(Admin.username == username))
        if user is None or len(password) < 12:
            raise click.ClickException("Unknown administrator or password shorter than 12 characters.")
        user.set_password(password)
        db.session.commit()
        click.echo("Password changed.")

    if app.config["AUTO_CREATE_DB"]:
        with app.app_context():
            db.create_all()
    return app
