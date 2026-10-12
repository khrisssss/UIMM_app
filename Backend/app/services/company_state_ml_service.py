import os
from datetime import datetime

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.score import Score
from app.models.axis import Axis


ML_ARTIFACT_DIR = "ml_artifacts"
MODEL_PATH = os.path.join(ML_ARTIFACT_DIR, "company_state_model.joblib")
METRICS_PATH = os.path.join(ML_ARTIFACT_DIR, "company_state_metrics.joblib")

AXIS_FEATURES = [
    "strategie_score",
    "performance_score",
    "marketing_score",
    "rh_score",
    "finance_score",
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

    if "finance" in axis_name:
        return "finance_score"

    if "digital" in axis_name or "num" in axis_name:
        return "digitalisation_score"

    if "rse" in axis_name or "csr" in axis_name:
        return "rse_score"

    return None


def encode_company_size(company_size):
    company_size = str(company_size or "").strip()

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
        .filter(Score.company_id == company_id)
        .all()
    )

    for score, axis in score_rows:
        feature_name = normalize_axis_name(axis.name)

        if feature_name:
            row[feature_name] = float(score.score_percentage or 0)

    return row


def training_dataset(db: Session):
    companies = (
        db.query(Company)
        .filter(
            Company.general_state.in_(["green", "orange", "red"]),
        )
        .all()
    )

    rows = []

    for company in companies:
        feature_row = get_company_feature_row(db, company.id)

        if feature_row is None:
            continue

        score_values = [feature_row[feature] for feature in AXIS_FEATURES]

        has_at_least_one_score = any(value > 0 for value in score_values)

        if not has_at_least_one_score:
            continue

        feature_row["target"] = company.general_state
        feature_row["company_id"] = company.id
        rows.append(feature_row)

    return pd.DataFrame(rows)


def build_demo_training_dataset():
    """
    Demo dataset used only when the real database does not yet contain
    enough completed diagnostics.

    This lets the ML pipeline work during development and certification demo.
    Later, the model should be retrained with real archived company data.
    """

    demo_rows = [
        # Good companies
        [90, 85, 80, 82, 75, 88, 78, "<10", "green"],
        [78, 82, 76, 80, 85, 79, 74, "11-50", "green"],
        [88, 90, 84, 86, 80, 83, 82, ">50", "green"],
        [72, 76, 70, 74, 78, 75, 73, "11-50", "green"],

        # To follow
        [60, 55, 48, 58, 62, 50, 55, "<10", "orange"],
        [55, 65, 42, 60, 58, 47, 50, "11-50", "orange"],
        [68, 52, 50, 55, 60, 45, 57, ">50", "orange"],
        [50, 58, 55, 52, 48, 60, 54, "11-50", "orange"],

        # Attention
        [35, 40, 28, 32, 45, 25, 38, "<10", "red"],
        [42, 35, 30, 38, 40, 32, 36, "11-50", "red"],
        [25, 30, 22, 28, 35, 20, 30, ">50", "red"],
        [45, 42, 25, 30, 38, 28, 34, "<10", "red"],
    ]

    rows = []

    for index, row in enumerate(demo_rows, start=1):
        feature_row = {
            "strategie_score": row[0],
            "performance_score": row[1],
            "marketing_score": row[2],
            "rh_score": row[3],
            "finance_score": row[4],
            "digitalisation_score": row[5],
            "rse_score": row[6],
        }

        feature_row.update(encode_company_size(row[7]))
        feature_row["target"] = row[8]
        feature_row["company_id"] = f"demo_{index}"

        rows.append(feature_row)

    return pd.DataFrame(rows)


def get_training_dataset(db: Session):
    real_dataset = training_dataset(db)

    if len(real_dataset) >= 9 and real_dataset["target"].nunique() >= 2:
        return real_dataset, "real_database"

    demo_dataset = build_demo_training_dataset()

    if len(real_dataset) > 0:
        combined_dataset = pd.concat([real_dataset, demo_dataset], ignore_index=True)
        return combined_dataset, "real_database_plus_demo_data"

    return demo_dataset, "demo_data_only"


def train_company_state_model(db: Session):
    os.makedirs(ML_ARTIFACT_DIR, exist_ok=True)

    dataset, dataset_source = get_training_dataset(db)

    X = dataset[FEATURE_COLUMNS]
    y = dataset["target"]

    if len(dataset) < 6:
        raise ValueError("Not enough training data to train the model.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y if y.nunique() > 1 else None,
    )

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)

    metrics = {
        "model_name": "company_state_prediction",
        "algorithm": "RandomForestClassifier",
        "accuracy": round(float(accuracy), 3),
        "trained_at": datetime.now().isoformat(),
        "dataset_size": int(len(dataset)),
        "dataset_source": dataset_source,
        "feature_columns": FEATURE_COLUMNS,
        "target": "general_state",
        "labels": STATE_LABELS,
        "classification_report": classification_report(
            y_test,
            y_pred,
            output_dict=True,
            zero_division=0,
        ),
    }

    joblib.dump(model, MODEL_PATH)
    joblib.dump(metrics, METRICS_PATH)

    return metrics


def load_model():
    if not os.path.exists(MODEL_PATH):
        return None

    return joblib.load(MODEL_PATH)


def load_metrics():
    if not os.path.exists(METRICS_PATH):
        return None

    return joblib.load(METRICS_PATH)


def predict_company_state(db: Session, company_id: int):
    model = load_model()

    if model is None:
        raise ValueError("Model not trained yet.")

    feature_row = get_company_feature_row(db, company_id)

    if feature_row is None:
        raise ValueError("Company not found.")

    X = pd.DataFrame([feature_row])[FEATURE_COLUMNS]

    predicted_state = model.predict(X)[0]

    probabilities = model.predict_proba(X)[0]
    classes = list(model.classes_)

    probability_by_class = {
        class_name: round(float(probability), 3)
        for class_name, probability in zip(classes, probabilities)
    }

    confidence = probability_by_class.get(predicted_state, 0)

    return {
        "company_id": company_id,
        "predicted_state": predicted_state,
        "predicted_state_label": STATE_LABELS.get(predicted_state, predicted_state),
        "confidence": confidence,
        "probabilities": {
            state: {
                "label": STATE_LABELS.get(state, state),
                "probability": probability,
            }
            for state, probability in probability_by_class.items()
        },
        "features_used": feature_row,
    }