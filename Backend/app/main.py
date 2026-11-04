from fastapi import FastAPI, Depends #main router
from app.monitoring import setup_logging, monitoring_middleware, metrics_endpoint
from app.routers import companies,axes,answers, scores, swots, reports, scoring, auth, users, company_profile, company_axes, admin_axis_questions
from app.routers import axis_question_categories

from app.database import Base, engine, get_db, SessionLocal


from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.financial_year import FinancialYear
from app.models.axis import Axis
from app.models.question import Question
from app.models.scoring_scale import ScoringScale
from app.models.scoring_level import ScoringLevel
from app.models.answer import Answer
from app.models.score import Score
from app.models.swot import SWOT
from app.models.reports import Report
from app.models.user import User
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.company_axis import CompanyAxis
from app.models.company_profile_section import CompanyProfileSection
from app.models.axis_question_category import AxisQuestionCategory

from fastapi.middleware.cors import CORSMiddleware #fpor the CORS issue when running frontend and backend on different ports




setup_logging()  # JSON logs for every module

app = FastAPI(
    title="UIMM API"
)

origins = [
    "http://localhost:5173",  # React frontend
    "http://127.0.0.1:5173",  # FastAPI backend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monitoring: log + count every request, expose metrics for Prometheus
app.middleware("http")(monitoring_middleware)
app.add_api_route("/metrics", metrics_endpoint, include_in_schema=False)

Base.metadata.create_all(bind=engine)

# Add the independent portfolio selection to databases created before this field existed.
with engine.begin() as connection:
    connection.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS is_synthetic BOOLEAN NOT NULL DEFAULT FALSE"))
    connection.execute(text("UPDATE companies SET is_synthetic = TRUE WHERE is_synthetic = FALSE AND (name LIKE 'DEMO ML - %' OR name LIKE 'DEMO — %')"))
    connection.execute(text("ALTER TABLE company_axes ADD COLUMN IF NOT EXISTS show_in_portfolio BOOLEAN NOT NULL DEFAULT FALSE"))
    connection.execute(text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS axis_analysis TEXT"))
    connection.execute(text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS presentation_content TEXT"))

# Retire Finance in existing installations without deleting historical records.
from app.services.diagnostic_scope_service import retire_finance
with SessionLocal.begin() as scope_db:
    retire_finance(scope_db)

@app.get("/")
def read_root():
    """Check that the API is running; returns a welcome message."""
    return {"message": "UIMM API is running!"}

@app.get("/db-test")
def test_db(db: Session = Depends(get_db)):
    """Check the database connection by running SELECT 1. Does not change database records."""
    result = db.execute(text("SELECT 1"))
    return {
        "database": "connected", 
        "result": result.scalar()}

app.include_router(companies.router)
app.include_router(axes.router)
app.include_router(answers.router)
app.include_router(scores.router)
app.include_router(swots.router)
app.include_router(reports.router)
app.include_router(scoring.router)
app.include_router(auth.router)
app.include_router(users.router)
# app.include_router(analysis.router)
app.include_router(company_profile.router)
app.include_router(company_axes.router)
app.include_router(admin_axis_questions.router)
app.include_router(axis_question_categories.router)


