"""Expose the public company data produced by the data pipeline (read-only)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_consultant_or_admin
from app.models.company import Company
from app.models.company_public_data import CompanyPublicData
from app.models.user import User
from app.schemas.company_public_data import CompanyPublicDataRead

router = APIRouter(tags=["Public company data"])


@router.get("/companies/{company_id}/public-data", response_model=CompanyPublicDataRead)
def read_company_public_data(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """Return the official public data of a company, found through its SIREN."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    if not company.siren:
        raise HTTPException(status_code=404, detail="This company has no SIREN yet")

    public_data = db.query(CompanyPublicData).filter(CompanyPublicData.siren == company.siren).first()
    if public_data is None:
        raise HTTPException(status_code=404, detail="No public data collected for this SIREN yet")
    return public_data


@router.get("/public-data", response_model=list[CompanyPublicDataRead])
def list_public_data(
    naf_code: Optional[str] = Query(None, description="Filter on an exact NAF code, e.g. 25.62B"),
    active_only: bool = Query(True, description="Only companies still active"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """List the collected public company data, with optional filters and pagination."""
    query = db.query(CompanyPublicData)
    if naf_code:
        query = query.filter(CompanyPublicData.naf_code == naf_code.upper())
    if active_only:
        query = query.filter(CompanyPublicData.is_active.is_(True))
    return query.order_by(CompanyPublicData.siren).offset(offset).limit(limit).all()
