"""Check that the real application (app/main.py) starts without crashing.

main.py runs PostgreSQL-only SQL when it starts (ADD COLUMN IF NOT EXISTS...),
so this test needs a real PostgreSQL database. Give its address in
TEST_POSTGRES_URL, for example:

    TEST_POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/uimm_test

Without TEST_POSTGRES_URL the test is skipped. Use an EMPTY test database:
never point it at the real one.

The app is started in a separate Python process, because the other tests
already loaded the database settings with SQLite.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

POSTGRES_URL = os.getenv("TEST_POSTGRES_URL")
BACKEND_DIR = Path(__file__).resolve().parents[1]

START_APP = """
from fastapi.testclient import TestClient
from app.main import app  # this line runs all the startup code of main.py

client = TestClient(app)
assert client.get("/").status_code == 200, "GET / failed"
assert client.get("/db-test").json() == {"database": "connected", "result": 1}, "GET /db-test failed"
assert client.get("/companies/").status_code == 401, "a protected route answered without login"
assert len(app.openapi()["paths"]) > 30, "routes are missing"
print("started")
"""


@pytest.mark.skipif(not POSTGRES_URL, reason="set TEST_POSTGRES_URL to an empty PostgreSQL database")
def test_app_starts_on_an_empty_database_and_restarts():
    env = {**os.environ, "DATABASE_URL": POSTGRES_URL, "SECRET_KEY": "test-secret-key-for-startup"}
    # Start twice: the first start creates the tables, the second checks that a restart works too.
    for attempt in ("first start", "restart"):
        result = subprocess.run([sys.executable, "-c", START_APP], cwd=BACKEND_DIR, env=env,
                                capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, f"{attempt} crashed:\n{result.stderr[-3000:]}"
        assert "started" in result.stdout
