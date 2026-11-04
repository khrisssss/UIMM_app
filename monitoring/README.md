# Monitoring UIMM Boost (Prometheus + Grafana)

## What is monitored

| Metric | Meaning | Alert threshold |
|---|---|---|
| `up{job="uimm_backend"}` | Prometheus can reach the API | `UimmApiDown`: 0 for 1 min |
| `uimm_http_requests_total` | Requests by method, route template, status | `UimmHighErrorRate`: > 5 % of 5xx over 5 min |
| `uimm_http_request_duration_seconds` | API response time | Dashboard only |
| `uimm_ai_calls_total` | Azure OpenAI calls by feature (`swot`, `report`) and outcome (`success`, `invalid_json`, `error`) | `UimmAiCallsFailing`: ≥ 3 failures in 15 min |
| `uimm_ai_call_duration_seconds` | Azure OpenAI latency | `UimmAiSlow`: p95 > 30 s for 10 min |
| `uimm_ai_tokens_total` | Input / output tokens (cost) | Dashboard only |
| `uimm_ai_draft_reviews_total` | AI SWOT drafts validated as-is vs edited by a consultant (feedback loop) | Dashboard only |

Logs are JSON lines on stdout (`docker compose logs backend`). They contain route templates and
technical IDs only: no names, e-mails, passwords, tokens or prompt content (RGPD).

## Run locally

1. Start the backend on port 8000: `cd Backend && uvicorn app.main:app --reload`
2. Check `http://127.0.0.1:8000/metrics` shows `uimm_` metrics.
3. Start the tools: `cd monitoring && docker compose -f docker-compose.monitoring.yml up -d`
4. Prometheus: http://127.0.0.1:9090 → Status → Targets: `uimm_backend` must be **UP**.
5. Grafana: http://127.0.0.1:3000 (admin / `GRAFANA_PASSWORD`, default `change-me`).
   The Prometheus data source is already configured.

## Check the configuration

```bash
docker run --rm -v "$PWD":/cfg --entrypoint promtool prom/prometheus:v3.5.0 check config /cfg/prometheus.yml
docker run --rm -v "$PWD":/cfg --entrypoint promtool prom/prometheus:v3.5.0 check rules /cfg/alert_rules.yml
```

## Test an alert

Stop the backend (Ctrl+C). After about 1 minute, `UimmApiDown` goes from *Pending* to *Firing*
in Prometheus → Alerts. Restart the backend: the alert resolves.

In production, `/api/metrics` is blocked by nginx so metrics are never public.
