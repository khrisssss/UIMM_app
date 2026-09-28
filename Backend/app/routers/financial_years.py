from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.dependencies.auth import require_consultant_or_admin
from app.models.company import Company
from app.models.financial_year import FinancialYear
from app.schemas.financial_year import FinancialYearInput, FinancialYearRead

router = APIRouter(prefix="/companies/{company_id}/financial-years", tags=["finance"])


def require_company(db, company_id):
    if db.get(Company, company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")


@router.get("", response_model=list[FinancialYearRead])
def list_years(company_id: int, db: Session = Depends(get_db), user=Depends(require_consultant_or_admin)):
    require_company(db, company_id)
    return db.query(FinancialYear).filter_by(company_id=company_id).order_by(FinancialYear.year, FinancialYear.kind).all()


@router.put("/{year}/{kind}", response_model=FinancialYearRead)
def save_year(company_id: int, year: int, kind: str, payload: FinancialYearInput, db: Session = Depends(get_db), user=Depends(require_consultant_or_admin)):
    require_company(db, company_id)
    if year != payload.year or kind != payload.kind:
        raise HTTPException(status_code=422, detail="Year and kind must match URL")
    record = db.query(FinancialYear).filter_by(company_id=company_id, year=year, kind=kind).first()
    if record is None:
        record = FinancialYear(company_id=company_id, year=year, kind=kind)
        db.add(record)
    for field, value in payload.model_dump().items():
        setattr(record, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Financial year already exists")
    db.refresh(record)
    return record


@router.delete("/{year}/{kind}", status_code=204)
def delete_year(company_id: int, year: int, kind: str, db: Session = Depends(get_db), user=Depends(require_consultant_or_admin)):
    record = db.query(FinancialYear).filter_by(company_id=company_id, year=year, kind=kind).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Financial year not found")
    db.delete(record)
    db.commit()
