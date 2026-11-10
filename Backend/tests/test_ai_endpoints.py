"""Tests for the AI endpoints (C9, C10, C12).

They call the real routes (generate a SWOT, validate it, generate a report)
with real login tokens. Only Azure OpenAI is replaced by a fake, so the tests
need no key, cost nothing and always give the same answer.
"""
import json
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.services.azure_openai_service as azure_service  # the file that talks to Azure OpenAI
import app.services.security as security  # makes and checks login tokens
from app.database import Base, get_db
from app.models.answer import Answer
from app.models.axis import Axis
from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.question import Question
from app.models.reports import Report  # noqa: F401  (needed so the table is created)
from app.models.score import Score
from app.models.swot import SWOT
from app.models.user import User
from app.routers import reports, swots

COMPANY_NAME = "Fonderie Secrète du Tarn"  # a name that must NEVER be sent to the AI

FAKE_SWOT = {  # what the fake AI answers when asked for a SWOT
    "strengths": ["Vision stratégique claire"],
    "weaknesses": ["Peu d'outils numériques"],
    "opportunities": ["Aides régionales à la modernisation"],
    "threats": ["Concurrence internationale"],
}

FAKE_REPORT = {  # what the fake AI answers when asked for a report
    "title": "Rapport de diagnostic — Entreprise anonymisée",
    "executive_summary": "Synthèse courte.",
    "diagnostic_summary": "Analyse globale.",
    "axis_analysis": {"Stratégie": {"strengths": ["Cap clair"], "weaknesses": [], "opportunities": [], "threats": []}},
    "presentation_content": {"activity": "Fonderie de pièces métalliques."},
    "swot_summary": "Forces\n- Vision",
    "recommendations": "Priorité 1 — Actions à court terme\n- Former les équipes",
    "conclusion": "Conclusion courte.",
}


@pytest.fixture
def db():
    """A fresh database in memory, shared by the test and by the API threads."""
    engine = create_engine(  # one database that lives only during the test
        "sqlite://",
        connect_args={"check_same_thread": False},  # the API runs in another thread
        poolclass=StaticPool,  # every thread sees the SAME database
    )

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")  # check links between tables, like PostgreSQL

    Base.metadata.create_all(engine)  # create every table
    with Session(engine) as session:
        yield session  # give the session to the test
    engine.dispose()  # throw the database away


@pytest.fixture
def ai_calls(monkeypatch):
    """Replace Azure OpenAI by a fake one and remember what was sent to it."""
    sent = []  # every message sent to the "AI" goes here

    def create(model, input):
        payload = input[1]["content"]  # the data part of the message (the second one)
        sent.append(payload)  # remember it so the test can read it
        answer = FAKE_REPORT if '"executive_summary"' in input[0]["content"] else FAKE_SWOT
        usage = SimpleNamespace(input_tokens=100, output_tokens=50)  # fake token counts
        return SimpleNamespace(output_text=json.dumps(answer), usage=usage)

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=create))
    monkeypatch.setattr(azure_service, "get_azure_client", lambda: fake_client)
    monkeypatch.setenv("AZURE_OPENAI_MODEL", "gpt-test")
    return sent


@pytest.fixture
def client(configured_db, monkeypatch):
    """A small app with only the SWOT and report routes, using the test database."""
    monkeypatch.setattr(security, "SECRET_KEY", "test-secret-key-for-ai-endpoints")
    api = FastAPI()
    api.include_router(swots.router)
    api.include_router(reports.router)
    api.dependency_overrides[get_db] = lambda: configured_db  # use the test database
    return TestClient(api)


@pytest.fixture
def company(configured_db):
    """A company with one answer and one score on every active axis."""
    db = configured_db
    company = Company(name=COMPANY_NAME, company_size="11-50", general_state="orange")
    db.add(company)
    db.flush()
    for axis in db.query(Axis).filter_by(is_active=True).all():
        question = Question(axis_id=axis.id, question_text=f"Question {axis.name}", max_score=5)
        db.add(question)
        db.flush()
        db.add(Answer(company_id=company.id, question_id=question.id, score_code="3", score_value=3))
        db.add(Score(company_id=company.id, axis_id=axis.id, score_percentage=60, score_total=3,
                     score_max=5, answered_questions=1, total_questions=1))
        db.add(CompanyAxis(company_id=company.id, axis_id=axis.id, is_selected=True, show_in_portfolio=True))
    db.commit()
    return company


def make_user(db, username, role="consultant", is_active=True):
    """Save a user and return the login header for them."""
    db.add(User(full_name=username, username=username, hashed_password="not-used",
                role=role, is_active=is_active))
    db.commit()
    token = security.create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


# ---------- Security: the AI is only reachable after login ----------

def test_ai_routes_refuse_requests_without_a_token(client, company, ai_calls):
    for url in (f"/companies/{company.id}/generate-swot", f"/companies/{company.id}/generate-report-draft"):
        assert client.post(url).status_code == 401  # no token: not logged in
    assert ai_calls == []  # the AI was never called


def test_ai_routes_refuse_a_fake_token(client, company, ai_calls):
    response = client.post(f"/companies/{company.id}/generate-swot",
                           headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"  # the text the frontend listens for
    assert ai_calls == []


def test_ai_routes_refuse_wrong_role_and_inactive_account(client, configured_db, company, ai_calls):
    viewer = make_user(configured_db, "viewer", role="viewer")
    sleeping = make_user(configured_db, "sleeping", is_active=False)
    assert client.post(f"/companies/{company.id}/generate-swot", headers=viewer).status_code == 403
    assert client.post(f"/companies/{company.id}/generate-swot", headers=sleeping).status_code == 403
    assert ai_calls == []


# ---------- SWOT: generate, read, validate ----------

def test_generate_swot_saves_an_ai_draft_without_sending_the_company_name(client, configured_db, company, ai_calls):
    headers = make_user(configured_db, "consultant")

    response = client.post(f"/companies/{company.id}/generate-swot", headers=headers)

    assert response.status_code == 200
    swot = response.json()
    assert swot["status"] == "draft"  # a human must still check it
    assert swot["generated_by_ai"] is True
    assert swot["strengths"] == "Vision stratégique claire"
    assert len(ai_calls) == 1  # exactly one AI call
    assert COMPANY_NAME not in ai_calls[0]  # the company name stayed on our server


def test_generated_swot_can_be_listed_then_validated(client, configured_db, company, ai_calls):
    headers = make_user(configured_db, "consultant")
    swot_id = client.post(f"/companies/{company.id}/generate-swot", headers=headers).json()["id"]

    listed = client.get(f"/companies/{company.id}/swot", headers=headers).json()
    assert [item["id"] for item in listed] == [swot_id]

    validated = client.patch(f"/companies/{company.id}/swot/{swot_id}", headers=headers,
                             json={"strengths": "Vision claire et partagée", "status": "validated"})
    assert validated.status_code == 200
    assert validated.json()["status"] == "validated"
    assert configured_db.get(SWOT, swot_id).strengths == "Vision claire et partagée"


def test_generating_twice_replaces_the_draft_instead_of_duplicating(client, configured_db, company, ai_calls):
    headers = make_user(configured_db, "consultant")
    first = client.post(f"/companies/{company.id}/generate-swot", headers=headers).json()
    second = client.post(f"/companies/{company.id}/generate-swot", headers=headers).json()
    assert first["id"] == second["id"]
    assert configured_db.query(SWOT).filter_by(company_id=company.id).count() == 1


# ---------- Report: generate a draft ----------

def test_generate_report_draft_restores_the_name_locally(client, configured_db, company, ai_calls):
    headers = make_user(configured_db, "consultant")

    response = client.post(f"/companies/{company.id}/generate-report-draft", headers=headers)

    assert response.status_code == 200
    report = response.json()
    assert report["title"] == f"Rapport de diagnostic — {COMPANY_NAME}"  # name added back after the AI call
    assert report["status"] == "draft"
    assert report["generated_by_ai"] is True
    axis_analysis = json.loads(report["axis_analysis"])  # saved as JSON text in the database
    assert axis_analysis["Stratégie"]["strengths"] == ["Cap clair"]
    assert COMPANY_NAME not in ai_calls[0]  # the AI only saw anonymous data


def test_unknown_company_gives_404_and_no_ai_call(client, configured_db, ai_calls):
    headers = make_user(configured_db, "consultant")
    assert client.post("/companies/999/generate-swot", headers=headers).status_code == 404
    assert client.post("/companies/999/generate-report-draft", headers=headers).status_code == 404
    assert ai_calls == []
