from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.axis import Axis
from app.models.swot import SWOT
from app.schemas.swot import SWOTCreate, SWOTRead

from app.models.answer import Answer
from app.models.question import Question
from app.models.score import Score
from app.models.scoring_scale import ScoringScale
from app.models.scoring_level import ScoringLevel
from app.services.swot_ai_service import generate_swot_draft
from app.services.swot_context import build_swot_context

router = APIRouter(
    prefix="/companies",
    tags=["SWOT"]
)


@router.post("/{company_id}/swot", response_model=SWOTRead)
def create_or_update_swot(
    company_id: int,
    swot_data: SWOTCreate,
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    if swot_data.axis_id is not None:
        axis = db.query(Axis).filter(Axis.id == swot_data.axis_id).first()

        if axis is None:
            raise HTTPException(
                status_code=404,
                detail="Axis not found"
            )

    existing_swot = (
        db.query(SWOT)
        .filter(
            SWOT.company_id == company_id,
            SWOT.axis_id == swot_data.axis_id
        )
        .first()
    )

    if existing_swot is None:
        new_swot = SWOT(
            company_id=company_id,
            axis_id=swot_data.axis_id,
            strengths=swot_data.strengths,
            weaknesses=swot_data.weaknesses,
            opportunities=swot_data.opportunities,
            threats=swot_data.threats,
            generation_source=swot_data.generation_source,
            generated_by_ai=swot_data.generated_by_ai,
            ai_model=swot_data.ai_model,
            status=swot_data.status
        )

        db.add(new_swot)
        db.commit()
        db.refresh(new_swot)

        return new_swot

    existing_swot.strengths = swot_data.strengths
    existing_swot.weaknesses = swot_data.weaknesses
    existing_swot.opportunities = swot_data.opportunities
    existing_swot.threats = swot_data.threats
    existing_swot.generation_source = swot_data.generation_source
    existing_swot.generated_by_ai = swot_data.generated_by_ai
    existing_swot.ai_model = swot_data.ai_model
    existing_swot.status = swot_data.status

    db.commit()
    db.refresh(existing_swot)

    return existing_swot


@router.get("/{company_id}/swot", response_model=list[SWOTRead])
def get_swots_by_company(
    company_id: int,
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    swots = (
        db.query(SWOT)
        .filter(SWOT.company_id == company_id)
        .order_by(SWOT.axis_id)
        .all()
    )

    return swots

@router.post("/{company_id}/generate-swot", response_model=SWOTRead)
def generate_swot(
    company_id: int,
    db: Session = Depends(get_db)
):
    swot_context = build_swot_context(company_id, db)

    generated_swot = generate_swot_draft(swot_context)

    existing_swot = (
        db.query(SWOT)
        .filter(
            SWOT.company_id == company_id,
            SWOT.axis_id == None
        )
        .first()
    )

    if existing_swot is None:
        new_swot = SWOT(
            company_id=company_id,
            axis_id=None,
            strengths=generated_swot["strengths"],
            weaknesses=generated_swot["weaknesses"],
            opportunities=generated_swot["opportunities"],
            threats=generated_swot["threats"],
            generation_source="fake_ai",
            generated_by_ai=True,
            ai_model="fake-generator-v1",
            status="draft"
        )

        db.add(new_swot)
        db.commit()
        db.refresh(new_swot)

        return new_swot

    existing_swot.strengths = generated_swot["strengths"]
    existing_swot.weaknesses = generated_swot["weaknesses"]
    existing_swot.opportunities = generated_swot["opportunities"]
    existing_swot.threats = generated_swot["threats"]
    existing_swot.generation_source = generated_swot["generation_source"]
    existing_swot.generated_by_ai = generated_swot["generated_by_ai"]
    existing_swot.ai_model = generated_swot["ai_model"]
    existing_swot.status = generated_swot["status"]

    db.commit()
    db.refresh(existing_swot)

    return existing_swot