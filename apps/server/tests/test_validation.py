"""Schema validation unit tests (no database)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sentinel_server.config import get_settings
from sentinel_server.validation import (
    SchemaValidationError,
    _load_registry,
    assert_project_consistency,
    validate_ingest_batch,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = REPO_ROOT / "packages" / "schema" / "jsonschema" / "v1"
FIXTURES = REPO_ROOT / "packages" / "schema" / "fixtures"


@pytest.fixture(autouse=True)
def _schema_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_SCHEMA_DIR", str(SCHEMA_DIR))
    get_settings.cache_clear()
    _load_registry.cache_clear()
    yield
    get_settings.cache_clear()
    _load_registry.cache_clear()


def test_valid_hello_batch() -> None:
    batch = json.loads(
        (FIXTURES / "valid" / "ingest-batch.hello.json").read_text(encoding="utf-8")
    )
    validate_ingest_batch(batch)
    assert_project_consistency(batch)


def test_empty_batch_fails() -> None:
    batch = json.loads(
        (FIXTURES / "invalid" / "ingest-batch.empty.json").read_text(encoding="utf-8")
    )
    with pytest.raises(SchemaValidationError):
        validate_ingest_batch(batch)
