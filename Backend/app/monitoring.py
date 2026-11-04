import json
import logging
import time
import uuid

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# ---------- 1. Logging: one JSON line per event ----------
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        log.update(getattr(record, "extra_fields", {}))
        return json.dumps(log, ensure_ascii=False)


def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


logger = logging.getLogger("uimm")


def log_event(level, message, **fields):
    logger.log(level, message, extra={"extra_fields": fields})


# ---------- 2. Metrics: numbers Prometheus will collect ----------
HTTP_REQUESTS = Counter(
    "uimm_http_requests_total", "HTTP requests", ["method", "route", "status"]
)
HTTP_DURATION = Histogram(
    "uimm_http_request_duration_seconds", "HTTP request duration", ["method", "route"]
)
AI_CALLS = Counter(
    "uimm_ai_calls_total", "Azure OpenAI calls", ["feature", "outcome"]
)
AI_DURATION = Histogram(
    "uimm_ai_call_duration_seconds", "Azure OpenAI call duration", ["feature"],
    buckets=(1, 2, 5, 10, 20, 30, 60, 120),
)
AI_TOKENS = Counter(
    "uimm_ai_tokens_total", "Tokens used by Azure OpenAI", ["feature", "type"]
)
AI_DRAFT_REVIEWS = Counter(
    "uimm_ai_draft_reviews_total", "Consultant review of AI drafts", ["feature", "result"]
)


# ---------- 3. Middleware: runs around every request ----------
async def monitoring_middleware(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration = time.perf_counter() - start
        route = request.scope.get("route")
        route_path = route.path if route else "unmatched"
        HTTP_REQUESTS.labels(request.method, route_path, str(status)).inc()
        HTTP_DURATION.labels(request.method, route_path).observe(duration)
        level = logging.ERROR if status >= 500 else logging.WARNING if status >= 400 else logging.INFO
        log_event(level, "http_request", request_id=request_id, method=request.method,
                  route=route_path, status=status, duration_ms=round(duration * 1000))


def metrics_endpoint():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
