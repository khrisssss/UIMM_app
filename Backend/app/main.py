from fastapi import FastAPI, Depends  # FastAPI builds the API; Depends = "run this first and give me the result"
from app.monitoring import setup_logging, monitoring_middleware, metrics_endpoint  # our logs and metrics (monitoring.py)
from app.routers import companies,axes,answers, scores, swots, reports, scoring, auth, users, company_profile, company_axes, admin_axis_questions  # the groups of routes
from app.routers import axis_question_categories, public_data  # two more groups of routes

from app.database import Base, engine, get_db, SessionLocal  # the database tools (database.py)


from sqlalchemy import text  # lets us write raw SQL as text
from sqlalchemy.orm import Session  # the type of a database session


from fastapi.middleware.cors import CORSMiddleware  # allows the frontend origin to call the API




setup_logging()  # from now on, every log line is written as JSON

app = FastAPI(  # create the API application
    title="UIMM API"  # the name shown on the /docs page
)

origins = [  # the websites allowed to call this API from a browser (CORS)
    "http://localhost:5173",  # the React frontend in development
    "http://127.0.0.1:5173",  # the same frontend, written with the IP address
]

app.add_middleware(  # add a layer that runs around every request
    CORSMiddleware,  # the CORS layer: tells the browser which websites may call us
    allow_origins=origins,  # only the websites listed above
    allow_credentials=True,  # allow the browser to send login information
    allow_methods=["*"],  # allow every method (GET, POST, PATCH, DELETE...)
    allow_headers=["*"],  # allow every header (including Authorization with the token)
)

# Monitoring: log + count every request, expose metrics for Prometheus
app.middleware("http")(monitoring_middleware)  # run our monitoring function around every request
app.add_api_route("/metrics", metrics_endpoint, include_in_schema=False)  # the page Prometheus reads; hidden from /docs

Base.metadata.create_all(bind=engine)  # create every table that does not exist yet (from models/*.py)

# Add the independent portfolio selection to databases created before this field existed.
with engine.begin() as connection:  # open one transaction: everything below is saved together
    connection.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS is_synthetic BOOLEAN NOT NULL DEFAULT FALSE"))  # add the "fictional company" column if it is missing
    connection.execute(text("UPDATE companies SET is_synthetic = TRUE WHERE is_synthetic = FALSE AND (name LIKE 'DEMO ML - %' OR name LIKE 'DEMO — %')"))  # mark old demo companies as fictional
    connection.execute(text("ALTER TABLE company_axes ADD COLUMN IF NOT EXISTS show_in_portfolio BOOLEAN NOT NULL DEFAULT FALSE"))  # add the "show in portfolio" column if missing
    connection.execute(text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS axis_analysis TEXT"))  # add the per-axis analysis column to reports if missing
    connection.execute(text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS presentation_content TEXT"))  # add the PowerPoint content column if missing
    # Public-data pipeline: SIREN link on companies, and indexes used by its SQL extraction.
    connection.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS siren VARCHAR(9)"))  # add the SIREN column if missing
    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_companies_siren ON companies (siren)"))  # an index = a sorted list that makes searching by SIREN fast
    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_scores_company_id ON scores (company_id)"))  # makes finding the scores of a company fast

# Retire Finance in existing installations without deleting historical records.
from app.services.diagnostic_scope_service import retire_finance  # the function that switches the Finance axis off
with SessionLocal.begin() as scope_db:  # open a session that saves automatically at the end
    retire_finance(scope_db)  # switch Finance off (old answers are kept)

@app.get("/")  # the route GET / (the home address of the API)
def read_root():
    """Check that the API is running; returns a welcome message."""
    return {"message": "UIMM API is running!"}  # a simple message: if you see it, the API is alive

@app.get("/db-test")  # the route GET /db-test, used by the deploy health check
def test_db(db: Session = Depends(get_db)):  # FastAPI gives us a database session
    """Check the database connection by running SELECT 1. Does not change database records."""
    result = db.execute(text("SELECT 1"))  # the smallest possible question to the database
    return {  # the answer
        "database": "connected",  # if we got here, the database answered
        "result": result.scalar()}  # the number 1 sent back by PostgreSQL

app.include_router(companies.router)  # plug in the company routes
app.include_router(axes.router)  # plug in the axis routes
app.include_router(answers.router)  # plug in the answer routes
app.include_router(scores.router)  # plug in the score routes
app.include_router(swots.router)  # plug in the SWOT routes
app.include_router(reports.router)  # plug in the report routes
app.include_router(scoring.router)  # plug in the scoring-scale routes
app.include_router(auth.router)  # plug in the login route
app.include_router(users.router)  # plug in the user-management routes
app.include_router(company_profile.router)  # plug in the company-profile routes
app.include_router(company_axes.router)  # plug in the "axes chosen for a company" routes
app.include_router(admin_axis_questions.router)  # plug in the question-management routes
app.include_router(axis_question_categories.router)  # plug in the question-category routes
app.include_router(public_data.router)  # plug in the public-data routes (pipeline and search)
