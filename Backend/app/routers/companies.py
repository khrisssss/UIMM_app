from fastapi import APIRouter, HTTPException, Depends #api router grouping routes together #Depends(get_db) → gives the route access to PostgreSQL
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.company import Company #database table model
from app.models.company import Company
from app.models.axis import Axis
from app.models.question import Question
from app.models.answer import Answer
from app.models.score import Score
from app.models.scoring_scale import ScoringScale
from app.models.scoring_level import ScoringLevel
from app.schemas.company import CompanyCreate, CompanyRead
from app.schemas.swot import SWOTContextRead
from app.services.swot_context import build_swot_context


router = APIRouter(
    prefix="/companies",
    tags=["companies"]
)


#fake_companies = [
#    {
#        "id": 1,
#        "name": "Company Test",
#        "address": "123 Main St",
#        "contact_name": "John Doe",
#        "email": "test@gmail.com",
#        "phone": "123456789",
#        "size": "<10",
#        "status": "prospect"
#    }
#]

fake_answers = [
    {
        "company_id": 1,
        "question_id": 1,
        "score": 4,
        "comment": "La direction a défini des priorités claires pour l'année."
    },
    {
        "company_id": 1,
        "question_id": 2,
        "score": 2,
        "comment": "Les objectifs ne sont pas encore bien partagés avec toutes les équipes."
    },
    {
        "company_id": 1,
        "question_id": 3,
        "score": 1,
        "comment": "L'entreprise utilise encore beaucoup de fichiers Excel."
    },
    {
        "company_id": 1,
        "question_id": 4,
        "score": 1,
        "comment": "Les données sont dispersées entre plusieurs outils."
    },
    {
        "company_id": 1,
        "question_id": 5,
        "score": 2,
        "comment": "Des actions RSE existent mais elles ne sont pas encore structurées."
    }
]


#@router.get("/", response_model=list[CompanyRead])
#def get_companies():
#    return [{ 
#        "id": 1,
#        "name": "Company Test",
#        "address": "123 Main St",
#        "contact_name": "John Doe",
#        "email": "test@gmail.com",
#        "phone": "123456789",
#        "size": "<10",
#        "status": "prospect"
#    }]

#@router.get("/{company_id}", response_model=CompanyRead)
#def get_company(company_id: int):
#    return {
#        "id": company_id,
#        "name": "Company Test",
#        "address": "123 Main St",
#        "contact_name": "John Doe",
#        "email": "test@gmail.com",
#        "phone": "123456789",
#        "size": "<10",
#        "status": "prospect"
#    }
@router.post("/", response_model=CompanyRead)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    new_company = Company(
        name=company.name,
        address=company.address,
        contact_name=company.contact_name,
        email=company.email,
        phone=company.phone,
        size=company.size,
        status=company.status
    )

    db.add(new_company)
    db.commit()
    db.refresh(new_company) #Refresh it to get the new ID

    return new_company

@router.get("/", response_model=list[CompanyRead])
def get_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).all()
    return companies
  

@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None: 
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )
    return company


@router.get("/{company_id}/swot-context", response_model=SWOTContextRead)
def get_swot_context(company_id: int, db: Session = Depends(get_db)):
    return build_swot_context(company_id, db)

