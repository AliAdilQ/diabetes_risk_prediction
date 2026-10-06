"""Database records. All timestamps are stored as naive UTC for portability."""

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Prediction(db.Model):
    __table_args__ = (
        db.CheckConstraint("prediction IN (0, 1)", name="valid_class"),
        db.CheckConstraint("probability >= 0 AND probability <= 1", name="valid_probability"),
    )
    id = db.Column(db.Integer, primary_key=True)
    pregnancies = db.Column(db.Integer, nullable=False)
    glucose = db.Column(db.Float, nullable=False)
    blood_pressure = db.Column(db.Float, nullable=False)
    skin_thickness = db.Column(db.Float, nullable=False)
    insulin = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    diabetes_pedigree = db.Column(db.Float, nullable=False)
    age = db.Column(db.Integer, nullable=False, index=True)
    prediction = db.Column(db.Integer, nullable=False, index=True)
    probability = db.Column(db.Float, nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    model_version = db.Column(db.String(64), nullable=False)
    source = db.Column(db.String(16), default="web", nullable=False)
    seed_key = db.Column(db.String(40), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False, index=True)

    @property
    def risk_label(self):
        return "Higher Predicted Risk" if self.prediction else "Lower Predicted Risk"

    @property
    def risk_key(self):
        return "higher_risk" if self.prediction else "lower_risk"
