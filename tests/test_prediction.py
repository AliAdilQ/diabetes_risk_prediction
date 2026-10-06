"""Inference, input boundaries, API contracts, and stored records."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.extensions import db
from app.features import FEATURES, FEATURE_COLUMNS
from app.ml_utils import get_artifact, infer, prepare_features
from app.models import Prediction
from scripts.generate_dummy_data import generate_dataset


def count_records(app):
    with app.app_context():
        return db.session.scalar(db.select(db.func.count(Prediction.id)))


def test_valid_prediction_saved(app, client, valid_inputs):
    response = client.post("/predict", data=valid_inputs)
    assert response.status_code == 302
    assert response.location.endswith("/prediction-result")
    result = client.get(response.location)
    assert "Estimated probability" in result.text
    assert "Predicted Risk" in result.text
    assert result.headers["Cache-Control"] == "no-store"
    with app.app_context():
        record = db.session.scalar(db.select(Prediction))
        expected = infer(valid_inputs)
        assert record.age == valid_inputs["age"]
        assert record.probability == pytest.approx(expected["probability"])
        assert record.prediction == expected["prediction"]
        assert record.model_version == expected["model_version"]


@pytest.mark.parametrize("feature", FEATURES, ids=lambda item: item.key)
@pytest.mark.parametrize("boundary", ["minimum", "maximum"])
def test_boundaries_are_valid(app, client, valid_inputs, feature, boundary):
    valid_inputs[feature.key] = getattr(feature, boundary)
    assert client.post("/predict", data=valid_inputs).status_code == 302
    assert count_records(app) == 1


@pytest.mark.parametrize("feature", FEATURES, ids=lambda item: item.key)
@pytest.mark.parametrize("direction", [-1, 1])
def test_out_of_range_not_saved(app, client, valid_inputs, feature, direction):
    valid_inputs[feature.key] = feature.minimum - 1 if direction < 0 else feature.maximum + 1
    assert client.post("/predict", data=valid_inputs).status_code == 422
    assert count_records(app) == 0


@pytest.mark.parametrize("value", ["", "not-a-number", "nan", "inf", "-inf"])
def test_malformed_numbers_not_saved(app, client, valid_inputs, value):
    valid_inputs["bmi"] = value
    assert client.post("/predict", data=valid_inputs).status_code == 422
    assert count_records(app) == 0


def test_whole_number_input(client, valid_inputs):
    valid_inputs["age"] = "35.5"
    assert client.post("/predict", data=valid_inputs).status_code == 422


def test_result_is_session_scoped(app, client, valid_inputs):
    client.post("/predict", data=valid_inputs)
    another_client = app.test_client()
    assert another_client.get("/prediction-result").status_code == 302
    assert another_client.get("/prediction-result/1").status_code == 404


def test_api_returns_same_prediction(app, client, valid_inputs):
    response = client.post("/api/predict", json=valid_inputs)
    assert response.status_code == 201
    assert response.json["prediction"] in {"lower_risk", "higher_risk"}
    assert 0 <= response.json["probability"] <= 1
    assert response.json["educational_only"] is True
    with app.app_context():
        assert response.json["probability"] == pytest.approx(infer(valid_inputs)["probability"])
        assert db.session.scalar(db.select(Prediction)).source == "api"


@pytest.mark.parametrize("patch", [{"age": True}, {"age": 35.5}, {"glucose": "120"},
                                  {"bmi": None}, {"bmi": float("nan")}, {"extra": 1},
                                  {"age": 999}, {"age": 10 ** 500},
                                  {"bmi": 10 ** 500}, {"age": 35.0, "bmi": 70.1}])
def test_api_invalid_inputs(app, client, valid_inputs, patch):
    valid_inputs.update(patch)
    assert client.post("/api/predict", json=valid_inputs).status_code == 422
    assert count_records(app) == 0


def test_api_object_and_content_type(client):
    assert client.post("/api/predict", json=[]).status_code == 400
    assert client.post("/api/predict", json={}).status_code == 422
    assert client.post("/api/predict", data="hello").status_code == 415
    assert client.post("/api/predict", data="{broken", content_type="application/json").status_code == 400


def test_api_integral_float_accepted(client, valid_inputs):
    valid_inputs["age"] = 35.0
    assert client.post("/api/predict", json=valid_inputs).status_code == 201


def test_csrf_is_enforced(app, client, valid_inputs):
    app.config["WTF_CSRF_ENABLED"] = True
    assert client.post("/predict", data=valid_inputs).status_code == 400
    assert client.post("/api/predict", json=valid_inputs).status_code == 400
    token = client.get("/api/csrf-token").json["csrf_token"]
    response = client.post("/api/predict", json=valid_inputs, headers={"X-CSRFToken": token})
    assert response.status_code == 201
    assert count_records(app) == 1


def test_synthetic_data_reproducible():
    pd.testing.assert_frame_equal(generate_dataset(), generate_dataset())
    assert len(generate_dataset()) >= 300
    assert set(generate_dataset().Outcome) == {0, 1}


def test_zero_cleanup_preserves_valid_zeros():
    frame = pd.DataFrame([{column: 0 for column in FEATURE_COLUMNS}])
    cleaned = prepare_features(frame)
    assert cleaned.Glucose.isna().all()
    assert cleaned.SkinThickness.isna().all()
    assert cleaned.Insulin.isna().all()
    assert cleaned.Pregnancies.iloc[0] == 0
    assert cleaned.DiabetesPedigreeFunction.iloc[0] == 0


def test_artifact_metrics_and_train_only_imputation(app):
    root = Path(__file__).resolve().parents[1]
    with app.app_context():
        artifact = get_artifact()
    metrics = json.loads((root / "models/model_metrics.json").read_text())
    assert len(metrics["models"]) == 4
    assert metrics["train_rows"] + metrics["test_rows"] == metrics["rows"]
    assert metrics["model_version"] == artifact["model_version"]
    from sklearn.model_selection import train_test_split
    from scripts.train_model import load_dataset
    features, labels = load_dataset(root / "data/diabetes_sample.csv")
    train, _, _, _ = train_test_split(features, labels, test_size=0.2, stratify=labels, random_state=42)
    np.testing.assert_allclose(artifact["pipeline"]["imputer"].statistics_, train.median().to_numpy())
    assert sum(sum(row) for row in metrics["confusion_matrix"]) == metrics["test_rows"]
