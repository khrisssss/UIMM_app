import logging

from app.monitoring import AI_DRAFT_REVIEWS, log_event
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import os
from app.database import get_db
from app.models.company import Company
from app.models.axis import Axis
from app.models.swot import SWOT
from app.schemas.swot import SWOTCreate, SWOTRead, SWOTUpdate 

from app.services.swot_context import build_swot_context

from app.models.user import User
from app.dependencies.auth import require_consultant_or_admin

from app.services.swot_ai_service import generate_swot_with_ai
from app.services.swot_ai_payload import make_swot_ai_payload
from app.services.swot_generation_service import normalize_ai_swot
router = APIRouter(
    prefix="/companies",
    tags=["SWOT"]
)

AI_FAILED_MESSAGE = "La génération par l'IA a échoué. Veuillez réessayer dans quelques instants."  # shown to the user

@router.post("/{company_id}/swot", response_model=SWOTRead)
def create_or_update_swot(
    company_id: int,
    swot_data: SWOTCreate,
    db: Session = Depends(get_db), current_user: User = Depends(require_consultant_or_admin)
):
    """Save MANUALLY written SWOT without calling AI. Creates a record or replaces the contents for the same company and axis. Omit axis_id for a company-wide SWOT; send status validated to save it as validated."""
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

    existing_swot = ( # this part only searches the database
        db.query(SWOT)
        .filter(
            SWOT.company_id == company_id,
            SWOT.axis_id == swot_data.axis_id
        )
        .first() # Find the first SWOT belonging to this company and this axis
    )

    if existing_swot is None: # if none it will create a new SWOT 
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

        db.add(new_swot) #Add the new record to the session 
        db.commit()   # Save the new record or the changes to PostgreSQL.
        db.refresh(new_swot)#Reload that record’s latest values from PostgreSQL nNOT refresh the whole database new_swot 

        return new_swot

    # if exist it will Replace a field on the existing record
    existing_swot.strengths = swot_data.strengths
    existing_swot.weaknesses = swot_data.weaknesses
    existing_swot.opportunities = swot_data.opportunities
    existing_swot.threats = swot_data.threats
    existing_swot.generation_source = swot_data.generation_source
    existing_swot.generated_by_ai = swot_data.generated_by_ai
    existing_swot.ai_model = swot_data.ai_model
    existing_swot.status = swot_data.status

    db.commit() # Save the new record or the changes to PostgreSQL. 
    db.refresh(existing_swot)  #Reload that record’s latest values from PostgreSQL nNOT refresh the whole database existing_swot

    return existing_swot #Send the updated SWOT back to whoever called the route. 


@router.get("/{company_id}/swot", response_model=list[SWOTRead])
def get_swots_by_company(
    company_id: int,
    db: Session = Depends(get_db), current_user: User = Depends(require_consultant_or_admin)
):
    """List saved SWOT records for the company, including company-wide and axis-specific records."""
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


@router.get("/{company_id}/swot-ai-payload")
def preview_swot_ai_payload(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """Preview the exact filtered user payload used for SWOT generation, without calling AI."""
    context = build_swot_context(db, company_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return make_swot_ai_payload(context)


@router.post("/{company_id}/generate-swot", response_model=SWOTRead)
def generate_swot(
    company_id: int,
    db: Session = Depends(get_db), current_user: User = Depends(require_consultant_or_admin)
):
    """Generate an AI SWOT from company diagnostic data and save it as a draft. Replaces an existing company-wide SWOT; its text can then be edited and saved."""
    swot_context = build_swot_context(db, company_id)
    
    if not swot_context:
        raise HTTPException(status_code=404, detail="Company not found")

    ai_payload = make_swot_ai_payload(swot_context)
    try:  # the AI is an outside service: it can be down, slow or answer badly
        raw_result = generate_swot_with_ai(ai_payload)  # ask Azure OpenAI for the SWOT
        if "raw_output" in raw_result:  # the AI did not answer with valid JSON
            raise ValueError("The AI answer is not valid JSON")
        ai_result = normalize_ai_swot(raw_result)  # check the shape: 4 lists of text
    except Exception as error:  # any problem: nothing is saved, the user gets a clear message
        log_event(logging.WARNING, "ai_generation_failed", feature="swot",
                  company_id=company_id, error_type=type(error).__name__)
        raise HTTPException(status_code=502, detail=AI_FAILED_MESSAGE)
    generation_source = "public_sources_ai" if ai_payload["evidence_basis"]["mode"] == "public_sources_only" else "azure_openai"

    strengths = ai_result.get("strengths", [])
    weaknesses = ai_result.get("weaknesses", [])
    opportunities = ai_result.get("opportunities", [])
    threats = ai_result.get("threats", [])

    existing_swot = (
        db.query(SWOT)
        .filter(
            SWOT.company_id == company_id,
            SWOT.axis_id == None,
        )
        .first()
    )

    if existing_swot is None:
        new_swot = SWOT(
            company_id=company_id,
            axis_id=None,
            strengths=strengths,
            weaknesses=weaknesses,
            opportunities=opportunities,
            threats=threats,
            generation_source=generation_source,
            generated_by_ai=True,
            ai_model=os.getenv("AZURE_OPENAI_MODEL", "azure-model"),
            status="draft",
        )

        db.add(new_swot)
        db.commit()
        db.refresh(new_swot)

        return new_swot

    existing_swot.strengths = strengths
    existing_swot.weaknesses = weaknesses
    existing_swot.opportunities = opportunities
    existing_swot.threats = threats
    existing_swot.generation_source = generation_source
    existing_swot.generated_by_ai = True
    existing_swot.ai_model = os.getenv("AZURE_OPENAI_MODEL", "azure-model")
    existing_swot.status = "draft"

    db.commit()
    db.refresh(existing_swot)

    return existing_swot

@router.patch("/{company_id}/swot/{swot_id}", response_model=SWOTRead)
def update_swot(
    company_id: int,
    swot_id: int,
    swot_data: SWOTUpdate,
    db: Session = Depends(get_db), current_user: User = Depends(require_consultant_or_admin)
):
    """Save edits to an existing SWOT. Works for manual and AI-generated records. Send status validated to validate it."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    swot = (
        db.query(SWOT)
        .filter(
            SWOT.id == swot_id,
            SWOT.company_id == company_id
        )
        .first()
    )

    if swot is None:
        raise HTTPException(
            status_code=404,
            detail="SWOT not found"
        )

    original_content = (swot.strengths, swot.weaknesses, swot.opportunities, swot.threats)
    was_validated = swot.status == "validated"

    if swot_data.strengths is not None:
        swot.strengths = swot_data.strengths

    if swot_data.weaknesses is not None:
        swot.weaknesses = swot_data.weaknesses

    if swot_data.opportunities is not None:
        swot.opportunities = swot_data.opportunities

    if swot_data.threats is not None:
        swot.threats = swot_data.threats

    if swot_data.status is not None:
        swot.status = swot_data.status

    # Feedback loop: how often consultants accept AI drafts as-is vs edit them
    if swot.generated_by_ai and swot.status == "validated" and not was_validated:
        new_content = (swot.strengths, swot.weaknesses, swot.opportunities, swot.threats)
        result = "accepted_as_is" if new_content == original_content else "edited"
        AI_DRAFT_REVIEWS.labels("swot", result).inc()
        log_event(logging.INFO, "ai_draft_reviewed", feature="swot", result=result,
                  swot_id=swot.id, company_id=company_id)

    db.commit()
    db.refresh(swot)

    return swot
