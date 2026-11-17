"""Tests for the company list (GET /companies/).

The companies page asks for every company and splits active / archived
itself, so the default answer must keep archived companies in the list.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.services.security as security
from app.database import Base, get_db
from app.models.company import Company
from app.models.user import User
from app.routers import companies


@pytest.fixture
def db():
    """A fresh in-memory database, shared by the test and by the API thread."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(db, monkeypatch):
    """A small app with only the company routes, logged in as a consultant."""
    monkeypatch.setattr(security, "SECRET_KEY", "test-secret-key-for-company-list")
    db.add(User(full_name="Consultant", username="consultant", hashed_password="not-used",
                role="consultant", is_active=True))
    db.add(Company(name="Active company", is_archived=False))
    db.add(Company(name="Archived company", is_archived=True))
    db.commit()

    api = FastAPI()
    api.include_router(companies.router)
    api.dependency_overrides[get_db] = lambda: db
    token = security.create_access_token({"sub": "consultant", "role": "consultant"})
    test_client = TestClient(api)
    test_client.headers["Authorization"] = f"Bearer {token}"
    return test_client


def names(response):
    assert response.status_code == 200
    return sorted(company["name"] for company in response.json())


def test_default_list_includes_archived_companies(client):
    assert names(client.get("/companies/")) == ["Active company", "Archived company"]


def test_include_archived_false_returns_only_active_companies(client):
    assert names(client.get("/companies/?include_archived=false")) == ["Active company"]


def test_include_archived_true_returns_every_company(client):
    assert names(client.get("/companies/?include_archived=true")) == ["Active company", "Archived company"]
