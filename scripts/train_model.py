"""Compare four pipelines on training folds; evaluate on a separate test set."""

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.features import FEATURE_COLUMNS  # noqa: E402
from app.ml_utils import prepare_features  # noqa: E402
from scripts.generate_dummy_data import generate_dataset  # noqa: E402

SEED = 42


def load_dataset(path):
    """Reject incompatible schemas; remove invalid targets and exact duplicates."""
    frame = pd.read_csv(path)
    required = FEATURE_COLUMNS + ["Outcome"]
    if not set(required).issubset(frame.columns):
        raise ValueError(f"Dataset requires columns: {', '.join(required)}")
    frame = frame[required].apply(pd.to_numeric, errors="coerce")
    frame = frame[frame.Outcome.isin([0, 1])].drop_duplicates()
    features = prepare_features(frame)
    # Negative feature values are invalid. Zero pregnancies and pedigree are valid.
    features = features.mask(features < 0)
    if len(frame) < 100 or frame.Outcome.value_counts().min() < 10:
        raise ValueError("Need at least 100 usable rows and 10 examples of each class.")
    if features.isna().all().any():
        raise ValueError("Every input column must have at least one valid measurement.")
    return features, frame.Outcome.astype(int)


def evaluate(pipeline, features, target):
    predicted = pipeline.predict(features)
    probability = pipeline.predict_proba(features)[:, 1]
    return {
        "accuracy": float(accuracy_score(target, predicted)),
        "precision": float(precision_score(target, predicted, zero_division=0)),
        "recall": float(recall_score(target, predicted, zero_division=0)),
        "f1_score": float(f1_score(target, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(target, probability)),
        "confusion_matrix": confusion_matrix(target, predicted, labels=[0, 1]).tolist(),
    }


def train():
    dataset = ROOT / "data" / "diabetes_sample.csv"
    dataset.parent.mkdir(parents=True, exist_ok=True)
    if not dataset.exists():
        generate_dataset().to_csv(dataset, index=False, lineterminator="\n")
    features, target = load_dataset(dataset)
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, stratify=target, random_state=SEED)
    estimators = {
        "Logistic Regression": LogisticRegression(max_iter=2000, random_state=SEED),
        "Random Forest": RandomForestClassifier(n_estimators=180, max_depth=7,
                                               min_samples_leaf=4, random_state=SEED, n_jobs=1),
        "Decision Tree": DecisionTreeClassifier(max_depth=5, min_samples_leaf=8,
                                                random_state=SEED),
        "K-Nearest Neighbors": KNeighborsClassifier(n_neighbors=15),
    }
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    comparisons = []
    pipelines = {}
    for name, estimator in estimators.items():
        steps = [("imputer", SimpleImputer(strategy="median"))]
        if name in {"Logistic Regression", "K-Nearest Neighbors"}:
            steps.append(("scaler", StandardScaler()))
        pipeline = Pipeline(steps + [("classifier", estimator)])
        scores = cross_validate(pipeline, x_train, y_train, cv=folds,
                                scoring={"auc": "roc_auc", "f1": "f1"}, n_jobs=1)
        pipeline.fit(x_train, y_train)
        comparisons.append({"name": name, "cv_roc_auc": float(scores["test_auc"].mean()),
                            "cv_roc_auc_std": float(scores["test_auc"].std()),
                            "cv_f1": float(scores["test_f1"].mean())})
        pipelines[name] = pipeline
    # Choose exclusively from training-fold scores. Holdout metrics never select the winner.
    comparisons.sort(key=lambda item: (item["cv_roc_auc"], item["cv_f1"]), reverse=True)
    name = comparisons[0]["name"]
    for comparison in comparisons:
        comparison.update(evaluate(pipelines[comparison["name"]], x_test, y_test))
    selected = comparisons[0]
    fingerprint = hashlib.sha256(dataset.read_bytes()).hexdigest()
    version = hashlib.sha256(f"{fingerprint}:{name}:{sklearn.__version__}:v1".encode()).hexdigest()[:16]
    metrics = {
        "selected_model": name, **{key: selected[key] for key in
            ("accuracy", "precision", "recall", "f1_score", "roc_auc", "confusion_matrix")},
        "cv_roc_auc": selected["cv_roc_auc"], "threshold": 0.5,
        "selection_method": "Highest mean ROC-AUC on 5 stratified training folds; F1 breaks ties",
        "models": comparisons, "dataset_type": "synthetic/demo", "random_state": SEED,
        "rows": len(features), "train_rows": len(x_train), "test_rows": len(x_test),
        "class_counts": {str(k): int(v) for k, v in target.value_counts().sort_index().items()},
        "dataset_sha256": fingerprint, "model_version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(), "sklearn_version": sklearn.__version__,
        "feature_columns": FEATURE_COLUMNS,
    }
    directory = ROOT / "models"
    directory.mkdir(parents=True, exist_ok=True)
    artifact = {"pipeline": pipelines[name], "model_name": name, "model_version": version,
                "sklearn_version": sklearn.__version__, "feature_columns": FEATURE_COLUMNS,
                "threshold": 0.5}
    # Each pipeline includes its fitted imputer and, where needed, scaler.
    temporary_model = directory / "diabetes_model.tmp"
    joblib.dump(artifact, temporary_model, compress=3)
    temporary_model.replace(directory / "diabetes_model.pkl")
    temporary_metrics = directory / "model_metrics.tmp"
    temporary_metrics.write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary_metrics.replace(directory / "model_metrics.json")
    print(f"Selected: {name} | CV AUC {selected['cv_roc_auc']:.3f}")
    print(f"Holdout: accuracy {selected['accuracy']:.3f}, precision {selected['precision']:.3f}, "
          f"recall {selected['recall']:.3f}, F1 {selected['f1_score']:.3f}, AUC {selected['roc_auc']:.3f}")
    return metrics


if __name__ == "__main__":
    train()
