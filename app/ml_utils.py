"""Trusted artifact loading and one inference path for web, API, and seed data."""

import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from flask import current_app

from .extensions import db
from .features import FEATURES, FEATURE_COLUMNS, ZERO_AS_MISSING
from .models import Prediction


class ModelUnavailable(RuntimeError):
    pass


def prepare_features(frame):
    """Deterministic cleanup only. Imputation/scaling remain inside each pipeline."""
    result = frame.loc[:, FEATURE_COLUMNS].copy().astype(float)
    result.replace([np.inf, -np.inf], np.nan, inplace=True)
    result[ZERO_AS_MISSING] = result[ZERO_AS_MISSING].replace(0, np.nan)
    return result


@lru_cache(maxsize=4)
def _load_artifact(path, modified_ns):
    # Only load artifacts shipped with, or trained by, this repository.
    artifact = joblib.load(path)
    if artifact.get("sklearn_version") != sklearn.__version__:
        raise ModelUnavailable("Model package version changed. Run python scripts/train_model.py.")
    if artifact.get("feature_columns") != FEATURE_COLUMNS:
        raise ModelUnavailable("Model feature schema changed. Retrain the model.")
    return artifact


def get_artifact():
    path = Path(current_app.config["MODEL_PATH"])
    try:
        return _load_artifact(str(path), path.stat().st_mtime_ns)
    except ModelUnavailable:
        raise
    except Exception as error:
        raise ModelUnavailable("Model unavailable. Run python scripts/train_model.py.") from error


def read_metrics():
    try:
        with Path(current_app.config["METRICS_PATH"]).open(encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError):
        return None


def infer(values):
    artifact = get_artifact()
    frame = pd.DataFrame([{feature.column: values[feature.key] for feature in FEATURES}])
    probability = float(artifact["pipeline"].predict_proba(prepare_features(frame))[0, 1])
    return {
        "prediction": int(probability >= artifact["threshold"]),
        "probability": probability,
        "model_name": artifact["model_name"],
        "model_version": artifact["model_version"],
    }


def save_prediction(values, source="web"):
    record = Prediction(**values, **infer(values), source=source)
    db.session.add(record)
    db.session.commit()
    return record
