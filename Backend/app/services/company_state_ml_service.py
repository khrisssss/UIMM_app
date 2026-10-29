import os
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import platform
import sklearn

import numpy as np

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.score import Score
from app.models.axis import Axis


ML_ARTIFACT_DIR = "ml_artifacts"
MODEL_PATH = os.path.join(ML_ARTIFACT_DIR, "company_state_model_six_axes.joblib")

AXIS_FEATURES = [
    "strategie_score",
    "performance_score",
    "marketing_score",
    "rh_score",
    "digitalisation_score",
    "rse_score",
]

FEATURE_COLUMNS = AXIS_FEATURES + [
    "company_size_less_10",
    "company_size_11_50",
    "company_size_more_50",
]

STATE_LABELS = {
    "green": "Bon",
    "orange": "À suivre",
    "red": "Attention",
}


def normalize_text(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def normalize_axis_name(axis_name):
    axis_name = normalize_text(axis_name)

    if "strat" in axis_name:
        return "strategie_score"

    if "performance" in axis_name:
        return "performance_score"

    if "marketing" in axis_name:
        return "marketing_score"

    if axis_name == "rh" or "ressources" in axis_name or "humain" in axis_name:
        return "rh_score"

    if "digital" in axis_name or "num" in axis_name:
        return "digitalisation_score"

    if "rse" in axis_name or "csr" in axis_name:
        return "rse_score"

    return None


def encode_company_size(company_size):
    company_size = str(company_size or "").strip()
    # The legacy application calls its smallest group <10; Power Apps says 1-10.
    if company_size == "1-10":
        company_size = "<10"

    return {
        "company_size_less_10": 1 if company_size == "<10" else 0,
        "company_size_11_50": 1 if company_size == "11-50" else 0,
        "company_size_more_50": 1 if company_size == ">50" else 0,
    }


def empty_feature_row():
    row = {}

    for feature in AXIS_FEATURES:
        row[feature] = 0.0

    row.update(
        {
            "company_size_less_10": 0,
            "company_size_11_50": 0,
            "company_size_more_50": 0,
        }
    )

    return row


def get_company_feature_row(db: Session, company_id: int):
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        return None

    row = empty_feature_row()
    row.update(encode_company_size(company.company_size))

    score_rows = (
        db.query(Score, Axis)
        .join(Axis, Score.axis_id == Axis.id)
        .filter(Score.company_id == company_id, Axis.is_active.is_(True))
        .all()
    )

    for score, axis in score_rows:
        feature_name = normalize_axis_name(axis.name)

        if feature_name:
            row[feature_name] = float(score.score_percentage or 0)

    return row


def is_demo_company(company):
    return bool(getattr(company, "is_synthetic", False)) or company.name.strip().upper().startswith("DEMO")


def training_dataset(db: Session, *, use_demo=False):
    """Archived, fully answered diagnostics only; never mix real and demo data.

    Real general_state labels must be reviewed by a consultant before archiving.
    A score of zero is valid. Absent axis scores remain zero in this model version.
    """
    companies = db.query(Company).filter(
        Company.general_state.in_(list(STATE_LABELS)), Company.is_archived.is_(True)
    ).order_by(Company.id).all()
    rows = []
    for company in companies:
        if is_demo_company(company) != use_demo:
            continue
        scores = db.query(Score).join(Axis, Score.axis_id == Axis.id).filter(Score.company_id == company.id, Axis.is_active.is_(True)).all()
        if not scores or any(s.total_questions <= 0 or s.answered_questions != s.total_questions for s in scores):
            continue
        if len({s.axis_id for s in scores}) != len(scores):
            raise ValueError(f"Duplicate axis scores for company {company.id}")
        feature_row = get_company_feature_row(db, company.id)
        feature_row["target"] = company.general_state
        feature_row["company_id"] = company.id
        rows.append(feature_row)
    return pd.DataFrame(rows, columns=FEATURE_COLUMNS + ["target", "company_id"])


def build_demo_training_dataset():
    """
    Small explicit synthetic fixture for automated tests and development.
    Never added automatically to a real database dataset.
    """

    demo_rows = [[90, 85, 80, 82, 88, 78, '<10', 'green'],
     [78, 82, 76, 80, 79, 74, '11-50', 'green'],
     [88, 90, 84, 86, 83, 82, '>50', 'green'],
     [72, 76, 70, 74, 75, 73, '11-50', 'green'],
     [60, 55, 48, 58, 50, 55, '<10', 'orange'],
     [55, 65, 42, 60, 47, 50, '11-50', 'orange'],
     [68, 52, 50, 55, 45, 57, '>50', 'orange'],
     [50, 58, 55, 52, 60, 54, '11-50', 'orange'],
     [35, 40, 28, 32, 25, 38, '<10', 'red'],
     [42, 35, 30, 38, 32, 36, '11-50', 'red'],
     [25, 30, 22, 28, 20, 30, '>50', 'red'],
     [45, 42, 25, 30, 28, 34, '<10', 'red']]

    rows = []

    for index, row in enumerate(demo_rows, start=1):
        feature_row = {
            "strategie_score": row[0],
            "performance_score": row[1],
            "marketing_score": row[2],
            "rh_score": row[3],
            "digitalisation_score": row[4],
            "rse_score": row[5],
        }

        feature_row.update(encode_company_size(row[6]))
        feature_row["target"] = row[7]
        feature_row["company_id"] = f"demo_{index}"

        rows.append(feature_row)

    return pd.DataFrame(rows)


def get_training_dataset(db: Session, *, use_demo=False):
    return training_dataset(db, use_demo=use_demo), "demo_database_only" if use_demo else "real_database"


def validate_training_dataset(dataset):
    required = FEATURE_COLUMNS + ["target", "company_id"]
    if any(column not in dataset.columns for column in required):
        raise ValueError("Missing training columns")
    if len(dataset) < 12:
        raise ValueError("At least 12 complete archived diagnostics are required. Use demo mode for fictional data.")
    if dataset[required].isna().any().any():
        raise ValueError("Missing training values")
    if dataset["company_id"].duplicated().any():
        raise ValueError("Duplicate company IDs: train/test leakage risk")
    if not dataset["target"].isin(STATE_LABELS).all():
        raise ValueError("Unknown target label")
    counts = dataset["target"].value_counts()
    if len(counts) < 2 or counts.min() < 4:
        raise ValueError("At least two states and four companies per state are required")
    try:
        values = dataset[FEATURE_COLUMNS].to_numpy(dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError("Features must be numeric") from error
    if not np.isfinite(values).all():
        raise ValueError("Features must be finite")
    if ((values[:, :len(AXIS_FEATURES)] < 0) | (values[:, :len(AXIS_FEATURES)] > 100)).any():
        raise ValueError("Axis scores must be between 0 and 100")
    sizes = values[:, len(AXIS_FEATURES):]
    if not np.isin(sizes, [0, 1]).all() or not (sizes.sum(axis=1) == 1).all():
        raise ValueError("Each company needs a known size: <10 / 1-10, 11-50 or >50")


def split_training_dataset(dataset):
    validate_training_dataset(dataset)
    return train_test_split(dataset, test_size=0.25, random_state=42, stratify=dataset["target"])


def artifact_path(use_demo=False):
    return Path(ML_ARTIFACT_DIR) / "company_state_demo_six_axes.joblib" if use_demo else Path(MODEL_PATH)


def train_model_from_dataset(dataset, *, dataset_source, use_demo=False):
    expected_source = "demo_database_only" if use_demo else "real_database"
    if dataset_source != expected_source:
        raise ValueError("Dataset source does not match the selected model mode")
    train, test = split_training_dataset(dataset)
    model = Pipeline(steps=[
        ("scaler", StandardScaler()),
        ("classifier", RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")),
    ])
    model.fit(train[FEATURE_COLUMNS], train["target"])
    predicted = model.predict(test[FEATURE_COLUMNS])
    labels = list(STATE_LABELS)
    metrics = {
        "model_name": "company_state_prediction",
        "feature_schema": "six_axes_v1",
        "algorithm": "RandomForestClassifier",
        "accuracy": round(float(accuracy_score(test["target"], predicted)), 3),
        "macro_f1": round(float(f1_score(test["target"], predicted, average="macro", zero_division=0)), 3),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_size": len(dataset), "dataset_source": dataset_source,
        "is_demo": use_demo,
        "evaluation_note": "Fictional data: pipeline demonstration only, not real-world model quality." if use_demo else "Holdout evaluation; labels require consultant review. Missing axes are encoded as zero.",
        "train_size": len(train), "test_size": len(test), "random_state": 42,
        "train_company_ids": train["company_id"].tolist(),
        "test_company_ids": test["company_id"].tolist(),
        "runtime_versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__, "joblib": joblib.__version__},
        "class_counts": {str(k): int(v) for k, v in dataset["target"].value_counts().items()},
        "feature_columns": FEATURE_COLUMNS, "target": "general_state", "labels": STATE_LABELS,
        "confusion_matrix_labels": labels,
        "confusion_matrix": confusion_matrix(test["target"], predicted, labels=labels).tolist(),
        "classification_report": classification_report(test["target"], predicted, labels=labels, output_dict=True, zero_division=0),
    }
    # One atomic bundle keeps a model and its metrics consistent. Demo artifacts
    # have their own path and can never replace the real model.
    destination = artifact_path(use_demo)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=destination.parent, suffix=".joblib")
    os.close(fd)
    try:
        joblib.dump({"model": model, "metrics": metrics}, temporary)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return metrics


def train_company_state_model(db: Session, *, use_demo=False):
    dataset, source = get_training_dataset(db, use_demo=use_demo)
    return train_model_from_dataset(dataset, dataset_source=source, use_demo=use_demo)


def load_bundle(use_demo=False):
    path = artifact_path(use_demo)
    return joblib.load(path) if path.exists() else None


def load_model(use_demo=False):
    bundle = load_bundle(use_demo)
    return bundle["model"] if bundle else None


def load_metrics(use_demo=False):
    bundle = load_bundle(use_demo)
    return bundle["metrics"] if bundle else None


def predict_company_state(db: Session, company_id: int):
    company = db.query(Company).filter_by(id=company_id).first()
    if company is None:
        raise ValueError("Company not found.")
    use_demo = is_demo_company(company)
    bundle = load_bundle(use_demo)
    if bundle is None:
        raise ValueError("Train the demo model first." if use_demo else "Train the real model first. Demo models are reserved for fictional companies.")
    feature_row = get_company_feature_row(db, company_id)
    if sum(encode_company_size(company.company_size).values()) != 1:
        raise ValueError("Unknown company size")
    model = bundle["model"]
    X = pd.DataFrame([feature_row])[FEATURE_COLUMNS]
    predicted_state = str(model.predict(X)[0])
    probabilities = {str(label): round(float(p), 3) for label, p in zip(model.classes_, model.predict_proba(X)[0])}
    return {
        "company_id": company_id,
        "predicted_state": predicted_state,
        "predicted_state_label": STATE_LABELS[predicted_state],
        "confidence": probabilities[predicted_state],
        "probabilities": {state: {"label": STATE_LABELS[state], "probability": probability} for state, probability in probabilities.items()},
        "features_used": feature_row,
        "is_demo": use_demo,
        "model_source": bundle["metrics"]["dataset_source"],
        "evaluation_note": bundle["metrics"]["evaluation_note"],
    }
