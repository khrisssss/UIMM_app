from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_consultant_or_admin
from app.models.user import User
from app.services.company_state_ml_service import (
    load_metrics,
    predict_company_state,
    train_company_state_model,
)


router = APIRouter(tags=["ML"])


@router.post("/ml/train-company-state-model")
def train_company_state_prediction_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """Train the company-state prediction model using eligible saved company data and return training metrics."""
    try:
        metrics = train_company_state_model(db)
        return {
            "message": "Company state prediction model trained successfully.",
            "metrics": metrics,
        }
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/ml/model-metrics")
def get_company_state_model_metrics(
    current_user: User = Depends(require_consultant_or_admin),
):
    """Read the saved model evaluation metrics. Returns 404 if no trained model metrics are available."""
    metrics = load_metrics()

    if metrics is None:
        raise HTTPException(
            status_code=404,
            detail="No trained model metrics found. Train the model first.",
        )

    return metrics


@router.post("/companies/{company_id}/predict-state")
def predict_company_general_state(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """Predict the company state using the trained model. Returns the predicted state and probabilities without applying the state to the company."""
    try:
        prediction = predict_company_state(db=db, company_id=company_id)
        return prediction
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))