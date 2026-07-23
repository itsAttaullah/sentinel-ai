"""Test fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sentinel_server.config import get_settings
from sentinel_server.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = REPO_ROOT / "packages" / "schema" / "jsonschema" / "v1"
FIXTURES = REPO_ROOT / "packages" / "schema" / "fixtures"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    db_path = tmp_path / "sentinel.db"
    monkeypatch.setenv("SENTINEL_DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("SENTINEL_SCHEMA_DIR", str(SCHEMA_DIR))
    monkeypatch.setenv("SENTINEL_AUTH_MODE", "local")
    get_settings.cache_clear()

    app = create_app(database_url=f"sqlite+pysqlite:///{db_path}")
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


@pytest.fixture()
def hello_batch() -> dict:
    return json.loads(
        (FIXTURES / "valid" / "ingest-batch.hello.json").read_text(encoding="utf-8")
    )
