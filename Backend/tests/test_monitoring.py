"""Tests for logging and monitoring (C11 / C20).

The Azure OpenAI client is replaced by a fake, so no real API call or key is needed.
"""
import os
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

import app.services.azure_openai_service as azure_service
from app.monitoring import metrics_endpoint, monitoring_middleware


def fake_client(output_text=None, error=None):
    def create(**kwargs):
        if error:
            raise error
        usage = SimpleNamespace(input_tokens=120, output_tokens=45)
        return SimpleNamespace(output_text=output_text, usage=usage)

    return lambda: SimpleNamespace(responses=SimpleNamespace(create=create))


def sample(name, labels):
    return REGISTRY.get_sample_value(name, labels) or 0


@pytest.fixture(autouse=True)
def model_name(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_MODEL", "gpt-test")


def test_successful_ai_call_is_counted(monkeypatch):
    before = sample("uimm_ai_calls_total", {"feature": "swot", "outcome": "success"})
    monkeypatch.setattr(azure_service, "get_azure_client", fake_client('{"strengths": ["Vision claire"]}'))

    result = azure_service.generate_json_response("prompt", {"company": 1}, feature="swot")

    assert result == {"strengths": ["Vision claire"]}
    assert sample("uimm_ai_calls_total", {"feature": "swot", "outcome": "success"}) == before + 1
    assert sample("uimm_ai_tokens_total", {"feature": "swot", "type": "input"}) >= 120


def test_invalid_json_is_counted_and_returns_fallback(monkeypatch):
    before = sample("uimm_ai_calls_total", {"feature": "report", "outcome": "invalid_json"})
    monkeypatch.setattr(azure_service, "get_azure_client", fake_client("Désolé, je ne peux pas."))

    result = azure_service.generate_json_response("prompt", {}, feature="report")

    assert result["raw_output"] == "Désolé, je ne peux pas."
    assert sample("uimm_ai_calls_total", {"feature": "report", "outcome": "invalid_json"}) == before + 1


def test_ai_error_is_counted_and_raised(monkeypatch):
    before = sample("uimm_ai_calls_total", {"feature": "swot", "outcome": "error"})
    monkeypatch.setattr(azure_service, "get_azure_client", fake_client(error=TimeoutError("Azure timeout")))

    with pytest.raises(TimeoutError):
        azure_service.generate_json_response("prompt", {}, feature="swot")

    assert sample("uimm_ai_calls_total", {"feature": "swot", "outcome": "error"}) == before + 1


def build_test_app():
    test_app = FastAPI()
    test_app.middleware("http")(monitoring_middleware)
    test_app.add_api_route("/metrics", metrics_endpoint)

    @test_app.get("/companies/{company_id}")
    def read_company(company_id: int):
        if company_id == 0:
            raise HTTPException(status_code=404, detail="Company not found")
        return {"id": company_id}

    return TestClient(test_app)


def test_requests_are_counted_by_route_template_not_id():
    client = build_test_app()
    labels = {"method": "GET", "route": "/companies/{company_id}", "status": "404"}
    before = sample("uimm_http_requests_total", labels)

    response = client.get("/companies/0")

    assert response.status_code == 404
    assert "X-Request-ID" in response.headers
    assert sample("uimm_http_requests_total", labels) == before + 1


def test_metrics_endpoint_exposes_prometheus_format():
    client = build_test_app()
    client.get("/companies/7")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "uimm_http_requests_total" in response.text
    assert "uimm_ai_calls_total" in response.text
