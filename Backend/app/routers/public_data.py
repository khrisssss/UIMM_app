"""Expose the public company data produced by the data pipeline (read-only)."""
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_consultant_or_admin
from app.models.company import Company
from app.models.company_public_data import CompanyPublicData
from app.models.user import User
from app.pipeline import config as pipeline_config
from app.pipeline.aggregate import normalize_headcount, normalize_naf, parse_date
from app.pipeline.extract_api import build_session, search_companies
from app.schemas.company_public_data import CompanyPublicDataRead, CompanySearchResult
from app.services.siren import normalize_siren

router = APIRouter(tags=["Public company data"])


def suggested_company_size(headcount_code: str | None) -> str | None:
    """Map the INSEE headcount bracket to the three sizes of the company form."""
    if headcount_code in ("00", "01", "02", "03"):
        return "<10"
    if headcount_code in ("11", "12"):
        return "11-50"
    if headcount_code and headcount_code.isdigit():
        return ">50"
    return None  # "NN" = unknown: the consultant chooses


@router.get("/public-data/search", response_model=list[CompanySearchResult])
def search_public_companies(
    q: str = Query(..., min_length=3, max_length=100, description="A SIREN or part of a company name"),
    current_user: User = Depends(require_consultant_or_admin),
):
    """Search the official company register live, to pre-fill the company creation form."""
    query = q.strip()
    try:
        siren = normalize_siren(query) if query.replace(" ", "").isdigit() else None
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    try:
        results = search_companies(build_session(retries_total=1), siren or query)
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Le service public de recherche d'entreprises ne répond pas. Réessayez dans un instant.")
    if siren:
        results = [result for result in results if result.get("siren") == siren]

    found = []
    for result in results:
        headcount = normalize_headcount(result.get("headcount_code"))
        state = result.get("administrative_state")
        found.append(CompanySearchResult(
            siren=result["siren"],
            legal_name=result.get("legal_name"),
            naf_code=normalize_naf(result.get("naf_code")),
            headcount_code=headcount,
            headcount_label=pipeline_config.HEADCOUNT_LABELS.get(headcount) if headcount else None,
            suggested_company_size=suggested_company_size(headcount),
            head_office_address=result.get("head_office_address"),
            postal_code=result.get("postal_code"),
            city=result.get("city"),
            creation_date=parse_date(result.get("creation_date")),
            is_active=None if state is None else state == "A",
        ))
    return found


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
