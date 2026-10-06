"""Idempotent local demo seeding; refuses to install demo credentials in production."""

import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.ml_utils import infer  # noqa: E402
from app.models import Admin, Prediction, utc_now  # noqa: E402


def seed_demo(app):
    with app.app_context():
        if app.config["ENVIRONMENT"] == "production":
            raise RuntimeError("Demo seeding is disabled in production. Use flask create-admin.")
        db.create_all()
        user = db.session.scalar(db.select(Admin).where(Admin.username == "admin"))
        if user is None:
            user = Admin(username="admin", email="admin@example.com")
            user.set_password("Admin@123")
            db.session.add(user)
        created = 0
        for index in range(24):
            key = f"demo-v1-{index:02d}"
            if db.session.scalar(db.select(Prediction).where(Prediction.seed_key == key)):
                continue
            high = index % 3 == 0
            values = {
                "pregnancies": index % 7, "glucose": 178 + index % 30 if high else 78 + index % 40,
                "blood_pressure": 65 + index % 25, "skin_thickness": 18 + index % 20,
                "insulin": 65 + index * 7, "bmi": round(36 + index % 7 if high else 21 + index % 9, 1),
                "diabetes_pedigree": round(0.2 + index % 8 * 0.12, 2), "age": 22 + index * 2,
            }
            record = Prediction(**values, **infer(values), source="demo", seed_key=key,
                                created_at=utc_now() - timedelta(days=index % 14, hours=index % 8))
            db.session.add(record)
            created += 1
        db.session.commit()
        return created


if __name__ == "__main__":
    application = create_app()
    try:
        count = seed_demo(application)
    except RuntimeError as error:
        raise SystemExit(str(error)) from error
    print(f"Added {count} demo predictions. Local admin: admin / Admin@123")
