"""Public pages and a CSRF-protected JSON prediction workflow."""

import math

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_wtf.csrf import generate_csrf
from werkzeug.datastructures import MultiDict

from .extensions import db, limiter
from .features import FEATURES
from .forms import PredictionForm
from .ml_utils import ModelUnavailable, get_artifact, read_metrics, save_prediction
from .models import Prediction

main = Blueprint("main", __name__)


@main.get("/")
def home():
    return render_template("index.html", metrics=read_metrics())


@main.route("/predict", methods=["GET", "POST"])
@limiter.limit("30 per minute", methods=["POST"])
def predict():
    form = PredictionForm()
    available = True
    try:
        get_artifact()
    except ModelUnavailable as error:
        available = False
        flash(str(error), "warning")
    if form.validate_on_submit():
        if not available:
            abort(503)
        values = {feature.key: getattr(form, feature.key).data for feature in FEATURES}
        record = save_prediction(values)
        session["last_prediction_id"] = record.id
        return redirect(url_for("main.result"))
    status = 422 if request.method == "POST" else 200
    return render_template("predict.html", form=form, available=available), status


@main.get("/prediction-result")
def result():
    record = db.session.get(Prediction, session.get("last_prediction_id", -1))
    if record is None:
        return redirect(url_for("main.predict"))
    return render_template("result.html", record=record)


@main.get("/about")
def about():
    return render_template("about.html")


@main.get("/model-info")
def model_info():
    return render_template("model_info.html", metrics=read_metrics())


@main.get("/api/csrf-token")
@limiter.limit("60 per minute")
def csrf_token():
    return jsonify(csrf_token=generate_csrf())


@main.post("/api/predict")
@limiter.limit("30 per minute")
def api_predict():
    if not request.is_json:
        return jsonify(error="Use Content-Type: application/json"), 415
    payload = request.get_json()
    if not isinstance(payload, dict):
        return jsonify(error="Expected a JSON object"), 400
    expected = {feature.key for feature in FEATURES}
    errors = {}
    if set(payload) - expected:
        errors["unknown_fields"] = ["Unexpected input fields."]
    for feature in FEATURES:
        value = payload.get(feature.key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors[feature.key] = ["Provide a JSON number."]
        elif isinstance(value, float) and not math.isfinite(value):
            errors[feature.key] = ["Provide a finite number."]
        elif feature.integer and value != int(value):
            errors[feature.key] = ["Provide a whole number."]
    if errors:
        return jsonify(error="Invalid inputs", fields=errors), 422
    normalized = {
        feature.key: int(payload[feature.key]) if feature.integer else payload[feature.key]
        for feature in FEATURES
    }
    form = PredictionForm(formdata=MultiDict({key: str(value) for key, value in normalized.items()}),
                          meta={"csrf": False})
    if not form.validate():
        return jsonify(error="Invalid inputs", fields=form.errors), 422
    try:
        record = save_prediction(normalized, source="api")
    except ModelUnavailable:
        return jsonify(error="Model unavailable. Train the model before predicting."), 503
    return jsonify(prediction=record.risk_key, probability=record.probability,
                   model=record.model_name, model_version=record.model_version,
                   educational_only=True), 201
