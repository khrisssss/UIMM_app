from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.axis import Axis
from app.database import get_db
from app.models.scoring_scale import ScoringScale
from app.models.scoring_level import ScoringLevel
from app.schemas.scoring import (
    ScoringScaleRead,
    ScoringScaleUpdate,
)

from app.models.user import User
from app.dependencies.auth import require_admin

router = APIRouter(
    tags=["Scoring"]
)




@router.patch("/scoring-scales/{scale_id}", response_model=ScoringScaleRead)
def update_scoring_scale(
    scale_id: int,
    scale_data: ScoringScaleUpdate,
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Edit an existing scoring scale and return it together with its scoring levels."""
    scale = db.query(ScoringScale).filter(ScoringScale.id == scale_id).first()

    if scale is None:
        raise HTTPException(
            status_code=404,
            detail="Scoring scale not found"
        )

    if scale_data.name is not None:
        scale.name = scale_data.name

    if scale_data.description is not None:
        scale.description = scale_data.description

    if scale_data.max_score is not None:
        scale.max_score = scale_data.max_score

    if scale_data.is_active is not None:
        scale.is_active = scale_data.is_active

    db.commit()
    db.refresh(scale)

    levels = (
        db.query(ScoringLevel)
        .filter(ScoringLevel.scoring_scale_id == scale.id)
        .order_by(ScoringLevel.order_index)
        .all()
    )

    return {
        "id": scale.id,
        "axis_id": scale.axis_id,
        "name": scale.name,
        "description": scale.description,
        "max_score": scale.max_score,
        "is_active": scale.is_active,
        "levels": levels
    }

@router.get("/scoring-scales", response_model=list[ScoringScaleRead])
def get_scoring_scales(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    scales = (
        db.query(ScoringScale)
        .order_by(ScoringScale.axis_id)
        .all()
    )

    result = []

    for scale in scales:
        levels = (
            db.query(ScoringLevel)
            .filter(ScoringLevel.scoring_scale_id == scale.id)
            .order_by(ScoringLevel.order_index)
            .all()
        )

        result.append(
            {
                "id": scale.id,
                "axis_id": scale.axis_id,
                "name": scale.name,
                "description": scale.description,
                "max_score": scale.max_score,
                "is_active": scale.is_active,
                "levels": levels,
            }
        )

    return result


@router.get("/axes/{axis_id}/scoring-scales", response_model=list[ScoringScaleRead])
def get_axis_scoring_scales(
    axis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    scales = (
        db.query(ScoringScale)
        .filter(ScoringScale.axis_id == axis_id)
        .order_by(ScoringScale.id)
        .all()
    )

    result = []

    for scale in scales:
        levels = (
            db.query(ScoringLevel)
            .filter(ScoringLevel.scoring_scale_id == scale.id)
            .order_by(ScoringLevel.order_index)
            .all()
        )

        result.append(
            {
                "id": scale.id,
                "axis_id": scale.axis_id,
                "name": scale.name,
                "description": scale.description,
                "max_score": scale.max_score,
                "is_active": scale.is_active,
                "levels": levels,
            }
        )

    return result


@router.patch("/scoring-levels/{level_id}")
def update_scoring_level(
    level_id: int,
    level_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    level = db.query(ScoringLevel).filter(ScoringLevel.id == level_id).first()

    if level is None:
        raise HTTPException(status_code=404, detail="Scoring level not found")

    if "code" in level_data:
        level.code = level_data["code"]

    if "label" in level_data:
        level.label = level_data["label"]

    if "score_value" in level_data:
        level.score_value = level_data["score_value"]

    if "description" in level_data:
        level.description = level_data["description"]

    if "order_index" in level_data:
        level.order_index = level_data["order_index"]

    if "is_active" in level_data:
        level.is_active = level_data["is_active"]

    db.commit()
    db.refresh(level)

    return level

@router.get("/axes/{axis_id}/scoring-scales", response_model=list[ScoringScaleRead])
def get_axis_scoring_scales(
    axis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    scales = (
        db.query(ScoringScale)
        .filter(ScoringScale.axis_id == axis_id)
        .order_by(ScoringScale.id)
        .all()
    )

    result = []

    for scale in scales:
        levels = (
            db.query(ScoringLevel)
            .filter(ScoringLevel.scoring_scale_id == scale.id)
            .order_by(ScoringLevel.order_index)
            .all()
        )

        result.append(
            {
                "id": scale.id,
                "axis_id": scale.axis_id,
                "name": scale.name,
                "description": scale.description,
                "max_score": scale.max_score,
                "is_active": scale.is_active,
                "levels": levels,
            }
        )

    return result

@router.post("/axes/{axis_id}/scoring-scales", response_model=ScoringScaleRead)
def create_axis_scoring_scale(
    axis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    axis = db.query(Axis).filter(Axis.id == axis_id).first()

    if axis is None:
        raise HTTPException(status_code=404, detail="Axis not found")

    existing_scale = (
        db.query(ScoringScale)
        .filter(ScoringScale.axis_id == axis_id)
        .first()
    )

    if existing_scale is not None:
        raise HTTPException(
            status_code=400,
            detail="This axis already has a scoring scale.",
        )

    max_score = 3 if axis.name.upper() == "RSE" else 5

    scale = ScoringScale(
        axis_id=axis_id,
        name=f"Scoring scale - {axis.name}",
        description=f"Default scoring scale for {axis.name}",
        max_score=max_score,
        is_active=True,
    )

    db.add(scale)
    db.commit()
    db.refresh(scale)

    default_levels = []

    if axis.name.upper() == "RSE":
        default_levels = [
            ("SO", "Sans objet", None, 1),
            ("0", "Non", 0, 2),
            ("1", "Partiellement", 1, 3),
            ("2", "Oui", 2, 4),
            ("3", "Oui avec preuves", 3, 5),
        ]
    else:
        default_levels = [
            ("0", "Non applicable", 0, 1),
            ("1", "Inexistant", 1, 2),
            ("2", "Informel", 2, 3),
            ("3", "En place mais partiel", 3, 4),
            ("4", "Structuré", 4, 5),
            ("5", "Optimisé et piloté", 5, 6),
        ]

    for code, label, score_value, order_index in default_levels:
        level = ScoringLevel(
            scoring_scale_id=scale.id,
            code=code,
            label=label,
            score_value=score_value,
            description=None,
            order_index=order_index,
        )

        db.add(level)

    db.commit()
    db.refresh(scale)

    levels = (
        db.query(ScoringLevel)
        .filter(ScoringLevel.scoring_scale_id == scale.id)
        .order_by(ScoringLevel.order_index)
        .all()
    )

    return {
        "id": scale.id,
        "axis_id": scale.axis_id,
        "name": scale.name,
        "description": scale.description,
        "max_score": scale.max_score,
        "is_active": scale.is_active,
        "levels": levels,
    }


@router.patch("/scoring-levels/{level_id}")
def update_scoring_level(
    level_id: int,
    level_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    level = db.query(ScoringLevel).filter(ScoringLevel.id == level_id).first()

    if level is None:
        raise HTTPException(status_code=404, detail="Scoring level not found")

    if "code" in level_data:
        level.code = level_data["code"]

    if "label" in level_data:
        level.label = level_data["label"]

    if "score_value" in level_data:
        level.score_value = level_data["score_value"]

    if "description" in level_data:
        level.description = level_data["description"]

    if "order_index" in level_data:
        level.order_index = level_data["order_index"]

    if "is_active" in level_data:
        level.is_active = level_data["is_active"]

    db.commit()
    db.refresh(level)

    return level