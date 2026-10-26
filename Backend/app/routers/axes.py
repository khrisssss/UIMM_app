from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.axis import Axis
from app.models.scoring_level import ScoringLevel
from app.models.scoring_scale import ScoringScale
from app.models.user import User


from app.schemas.scoring import ScoringScaleRead
from app.schemas.axis import AxisRead, AxisUpdate

from app.dependencies.auth import require_admin, require_consultant_or_admin


router = APIRouter(
    prefix="/axes",
    tags=["Axes"],
)


@router.get("/", response_model=list[AxisRead])
def get_axes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """List active diagnostic axes in display order."""
    axes = (
        db.query(Axis)
        .filter(Axis.is_active == True)
        .order_by(Axis.order_index)
        .all()
    )

    return axes


@router.patch("/{axis_id}", response_model=AxisRead)
def update_axis(
    axis_id: int,
    axis_data: AxisUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Edit an existing axis, including its name, description, display order, or active status."""
    axis = db.query(Axis).filter(Axis.id == axis_id).first()

    if axis is None:
        raise HTTPException(
            status_code=404,
            detail="Axis not found",
        )

    update_data = axis_data.model_dump(exclude_unset=True)
    from app.services.diagnostic_scope_service import is_finance_name
    if is_finance_name(axis.name) or is_finance_name(update_data.get("name", "")):
        raise HTTPException(status_code=400, detail="Finance is no longer a diagnostic axis")

    for key, value in update_data.items():
        setattr(axis, key, value)

    db.commit()
    db.refresh(axis)

    return axis


@router.get("/{axis_id}/scoring-scales", response_model=ScoringScaleRead)
def get_scoring_scales_by_axis(
    axis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """Read the active scoring scale and its answer levels for an axis. Returns 404 when no active scale exists."""
    axis = db.query(Axis).filter(Axis.id == axis_id).first()

    if axis is None or not axis.is_active:
        raise HTTPException(
            status_code=404,
            detail="Axis not found",
        )

    scoring_scale = (
        db.query(ScoringScale)
        .filter(
            ScoringScale.axis_id == axis_id,
            ScoringScale.is_active == True,
        )
        .first()
    )

    if scoring_scale is None:
        raise HTTPException(
            status_code=404,
            detail="No scoring scales found for this axis",
        )

    levels = (
        db.query(ScoringLevel)
        .filter(ScoringLevel.scoring_scale_id == scoring_scale.id)
        .order_by(ScoringLevel.order_index)
        .all()
    )

    return {
        "id": scoring_scale.id,
        "axis_id": scoring_scale.axis_id,
        "name": scoring_scale.name,
        "description": scoring_scale.description,
        "max_score": scoring_scale.max_score,
        "is_active": scoring_scale.is_active,
        "levels": levels,
    }
