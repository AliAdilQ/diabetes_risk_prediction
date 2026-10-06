"""Protected analytics and paginated prediction management."""

import csv
import io
from datetime import datetime, timedelta
from urllib.parse import urlsplit

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import case, func, or_

from .extensions import db, limiter
from .forms import ActionForm, LoginForm
from .ml_utils import read_metrics
from .models import Admin, Prediction, utc_now

admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.context_processor
def action_context():
    return {"action_form": ActionForm()}


@admin.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(Admin).where(Admin.username == form.username.data))
        if user and user.check_password(form.password.data):
            session.clear()
            login_user(user)
            session.permanent = True
            destination = request.args.get("next", "")
            parsed = urlsplit(destination)
            if (parsed.scheme or parsed.netloc or not destination.startswith("/admin")
                    or destination.startswith("//") or "\\" in destination):
                destination = url_for("admin.dashboard")
            return redirect(destination)
        flash("Username or password is incorrect.", "danger")
        return render_template("admin/login.html", form=form), 401
    return render_template("admin/login.html", form=form)


@admin.post("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("admin.login"))


@admin.get("")
@admin.get("/")
@login_required
def dashboard():
    today = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    total, higher, average, today_count = db.session.execute(db.select(
        func.count(Prediction.id),
        func.sum(case((Prediction.prediction == 1, 1), else_=0)),
        func.avg(Prediction.probability),
        func.sum(case((Prediction.created_at >= today, 1), else_=0)),
    )).one()
    higher = higher or 0
    start = today - timedelta(days=13)
    daily_rows = db.session.execute(db.select(
        func.date(Prediction.created_at), func.count(Prediction.id)
    ).where(Prediction.created_at >= start).group_by(func.date(Prediction.created_at))).all()
    daily = {str(day): count for day, count in daily_rows}
    days = [start + timedelta(days=index) for index in range(14)]
    age_group = case(
        (Prediction.age < 30, "18–29"), (Prediction.age < 45, "30–44"),
        (Prediction.age < 60, "45–59"), else_="60+"
    )
    ages = dict(db.session.execute(
        db.select(age_group, func.count(Prediction.id)).group_by(age_group)
    ).all())
    chart_data = {
        "risk": [total - higher, higher],
        "days": [day.strftime("%b %d") for day in days],
        "counts": [daily.get(day.strftime("%Y-%m-%d"), 0) for day in days],
        "ageLabels": ["18–29", "30–44", "45–59", "60+"],
        "ageCounts": [ages.get(label, 0) for label in ["18–29", "30–44", "45–59", "60+"]],
    }
    recent = db.session.scalars(db.select(Prediction).order_by(
        Prediction.created_at.desc(), Prediction.id.desc()).limit(6)).all()
    stats = {"total": total, "higher": higher, "lower": total - higher,
             "average": average or 0, "today": today_count or 0}
    return render_template("admin/dashboard.html", stats=stats, charts=chart_data, recent=recent)


def prediction_query():
    """All filters are typed or allowlisted; SQLAlchemy binds user values."""
    query = db.select(Prediction)
    search = request.args.get("q", "").strip()[:100]
    risk = request.args.get("risk", "")
    if search:
        conditions = [Prediction.model_name.ilike(f"%{search}%")]
        if search.isdigit():
            conditions.extend([Prediction.id == int(search), Prediction.age == int(search)])
        query = query.where(or_(*conditions))
    if risk in {"0", "1"}:
        query = query.where(Prediction.prediction == int(risk))
    for parameter, lower in (("from", True), ("to", False)):
        value = request.args.get(parameter, "")
        if not value:
            continue
        try:
            date = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            abort(400)
        query = query.where(Prediction.created_at >= date if lower else
                            Prediction.created_at < date + timedelta(days=1))
    sort = request.args.get("sort", "newest")
    columns = {
        "newest": Prediction.created_at.desc(), "oldest": Prediction.created_at.asc(),
        "probability": Prediction.probability.desc(), "age": Prediction.age.asc(),
        "glucose": Prediction.glucose.desc(),
    }
    return query.order_by(columns.get(sort, columns["newest"]), Prediction.id.desc())


@admin.get("/predictions")
@login_required
def predictions():
    page = max(1, request.args.get("page", 1, type=int))
    pagination = db.paginate(prediction_query(), page=page, per_page=12, error_out=False)
    parameters = request.args.to_dict()
    parameters.pop("page", None)
    return render_template("admin/predictions.html", pagination=pagination, parameters=parameters)


@admin.get("/predictions/<int:prediction_id>")
@login_required
def prediction_detail(prediction_id):
    record = db.get_or_404(Prediction, prediction_id)
    return render_template("admin/prediction_detail.html", record=record)


@admin.post("/predictions/<int:prediction_id>/delete")
@login_required
def delete_prediction(prediction_id):
    record = db.get_or_404(Prediction, prediction_id)
    db.session.delete(record)
    db.session.commit()
    flash(f"Prediction #{prediction_id} deleted.", "success")
    return redirect(url_for("admin.predictions"))


@admin.get("/predictions/export")
@login_required
@limiter.limit("10 per minute")
def export_predictions():
    output = io.StringIO()
    writer = csv.writer(output)
    columns = ["id", "pregnancies", "glucose", "blood_pressure", "skin_thickness", "insulin",
               "bmi", "diabetes_pedigree", "age", "prediction", "probability", "created_at"]
    writer.writerow(columns)
    for record in db.session.scalars(prediction_query()):
        writer.writerow([getattr(record, column) for column in columns])
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=predictions.csv"})


@admin.get("/model-performance")
@login_required
def model_performance():
    return render_template("admin/model_performance.html", metrics=read_metrics())
