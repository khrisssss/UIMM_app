from fastapi import FastAPI, Depends #main router
from app.routers import companies,axes,answers, scores, swots

from app.database import Base, engine, get_db


from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.axis import Axis
from app.models.question import Question
from app.models.scoring_scale import ScoringScale
from app.models.scoring_level import ScoringLevel
from app.models.answer import Answer
from app.models.score import Score
from app.models.swot import SWOT


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="UIMM API"
)

@app.get("/")
def read_root():
    return {"message": "UIMM API is running!"}

@app.get("/db-test")
def test_db(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    return {
        "database": "connected", 
        "result": result.scalar()}

app.include_router(companies.router)
app.include_router(axes.router)
app.include_router(answers.router)
app.include_router(scores.router)
app.include_router(swots.router)