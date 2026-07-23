"""API integration tests (SQLite)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

FIXTURES = Path(__file__).resolve().parents[3] / "packages" / "schema" / "fixtures"


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_and_get_run(client: TestClient, hello_batch: dict) -> None:
    response = client.post("/v1/ingest", json=hello_batch)
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["accepted"] is True
    assert body["counts"]["runs"] == 1
    assert body["counts"]["spans"] == 3
    assert body["counts"]["events"] == 1

    detail = client.get("/v1/projects/proj_demo/runs/run_hello_001")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["run"]["run_id"] == "run_hello_001"
    assert len(payload["spans"]) == 3
    assert len(payload["events"]) == 1

    listed = client.get("/v1/projects/proj_demo/runs")
    assert listed.status_code == 200
    assert any(item["run_id"] == "run_hello_001" for item in listed.json()["items"])


def test_ingest_is_idempotent(client: TestClient, hello_batch: dict) -> None:
    assert client.post("/v1/ingest", json=hello_batch).status_code == 202
    # mutate status on re-send
    hello_batch["runs"][0]["status"] = "failed"
    hello_batch["runs"][0]["ended_at"] = "2026-07-23T09:15:40.000Z"
    assert client.post("/v1/ingest", json=hello_batch).status_code == 202

    detail = client.get("/v1/projects/proj_demo/runs/run_hello_001").json()
    assert detail["run"]["status"] == "failed"


def test_invalid_batch_is_quarantined(client: TestClient) -> None:
    bad = json.loads(
        (FIXTURES / "invalid" / "ingest-batch.empty.json").read_text(encoding="utf-8")
    )
    response = client.post("/v1/ingest", json=bad)
    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "SCHEMA_VALIDATION_FAILED"

    quarantine = client.get("/v1/quarantine")
    assert quarantine.status_code == 200
    items = quarantine.json()["items"]
    assert items
    assert items[0]["error_code"] == "SCHEMA_VALIDATION_FAILED"


def test_create_and_get_project(client: TestClient) -> None:
    created = client.post("/v1/projects", json={"id": "proj_x", "name": "Example"})
    assert created.status_code == 201
    fetched = client.get("/v1/projects/proj_x")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Example"
