from fastapi import APIRouter, HTTPException, Depends #api router grouping routes together #Depends(get_db) → gives the route access to PostgreSQL
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.company import Company #database table model

from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.services.swot_context import build_swot_context
from app.services.company_details_service import build_company_details

from app.models.user import User
from app.dependencies.auth import require_consultant_or_admin

from app.models.answer import Answer
from app.models.score import Score
from app.models.swot import SWOT
from app.models.reports import Report
from app.models.company_axis import CompanyAxis
from app.models.company_profile_answer import CompanyProfileAnswer


router = APIRouter(
    prefix="/companies",
    tags=["companies"]
)


@router.post("/", response_model=CompanyRead)
def create_company(company: CompanyCreate, db: Session = Depends(get_db), current_user: User = Depends(require_consultant_or_admin)):
    """Create a company record from the supplied company information."""
    new_company = Company(
        name=company.name,
        status=company.status,

        contact_name=company.contact_name,
        contact_email=company.contact_email,
        contact_phone=company.contact_phone,

        address=company.address,
        company_size=company.company_size,

        prediag_origin=company.prediag_origin,
        prediag_origin_other=company.prediag_origin_other,

        has_rse=company.has_rse,
        specific_regulatory_constraints=company.specific_regulatory_constraints,

        general_comment=company.general_comment,
        )

    db.add(new_company)
    db.commit()
    db.refresh(new_company) #Refresh it to get the new ID

    return new_company

@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    db: Session = Depends(get_db), current_user: User = Depends(require_consultant_or_admin)
):
    """Edit a company record, including its archive status and general state when supplied."""
    db_company = db.query(Company).filter(Company.id == company_id).first()

    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = company_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_company, key, value)

    db.commit()
    db.refresh(db_company)

    return db_company

@router.get("/", response_model=list[CompanyRead])
def get_companies(
    include_archived: bool = False,
    db: Session = Depends(get_db), current_user: User = Depends(require_consultant_or_admin)
):
    """List company records accessible through this endpoint."""
    query = db.query(Company)

    if include_archived :
        query = query.filter(Company.is_archived == False)

    companies = query.order_by(Company.created_at.desc()).all()

    return companies
  

@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_consultant_or_admin)):
    """Read one company by its ID. Returns 404 if it does not exist."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None: 
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )
    return company


@router.get("/{company_id}/swot-context")
def get_swot_context(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_consultant_or_admin)):
    """Preview the full local SWOT context. This is not the filtered AI payload."""
    context = build_swot_context(db, company_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return context


# Path is relative to the router prefix "/companies".
@router.delete("/{company_id}/hard-delete")
def hard_delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_consultant_or_admin),
):
    """Permanently delete the company and its associated answers, scores, SWOT records, reports, profile answers, and axis selections."""
    db_company = db.query(Company).filter(Company.id == company_id).first()

    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")

    deleted_profile_answers = (
        db.query(CompanyProfileAnswer)
        .filter(CompanyProfileAnswer.company_id == company_id)
        .delete(synchronize_session=False)
    )

    deleted_answers = (
        db.query(Answer)
        .filter(Answer.company_id == company_id)
        .delete(synchronize_session=False)
    )

    deleted_scores = (
        db.query(Score)
        .filter(Score.company_id == company_id)
        .delete(synchronize_session=False)
    )

    deleted_swots = (
        db.query(SWOT)
        .filter(SWOT.company_id == company_id)
        .delete(synchronize_session=False)
    )

    deleted_reports = (
        db.query(Report)
        .filter(Report.company_id == company_id)
        .delete(synchronize_session=False)
    )

    deleted_company_axes = (
        db.query(CompanyAxis)
        .filter(CompanyAxis.company_id == company_id)
        .delete(synchronize_session=False)
    )

    db.delete(db_company)
    db.commit()

    return {
        "message": "Company and all related data permanently deleted",
        "company_id": company_id,
        "deleted_profile_answers": deleted_profile_answers,
        "deleted_diagnostic_answers": deleted_answers,
        "deleted_scores": deleted_scores,
        "deleted_swots": deleted_swots,
        "deleted_reports": deleted_reports,
        "deleted_company_axes": deleted_company_axes,
    }


@router.get("/{company_id}/all-details")
def get_all_details_of_a_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """Read all company details, including unanswered/inactive questions and all axes.
    
    Includes personal information for internal viewing; never sends data to AI.
    Selection flags identify diagnostic axes.
    """
    details = build_company_details(db, company_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return details
