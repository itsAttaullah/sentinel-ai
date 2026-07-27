"""Tests for redaction and scoped API keys."""

from __future__ import annotations

from copy import deepcopy

from fastapi.testclient import TestClient

from sentinel_server.main import create_app
from sentinel_server.services.redaction import redact_ingest_batch


def test_redact_default_masks_llm_content_and_secrets() -> None:
    batch = {
        "runs": [{"attributes": {"api_key": "secret", "task": "ok"}}],
        "spans": [
            {
                "kind": "llm",
                "llm": {
                    "provider": "openai",
                    "model": "gpt",
                    "messages": [{"role": "user", "content": "ssn 123"}],
                    "response": {"role": "assistant", "content": "answer"},
                },
            },
            {
                "kind": "tool",
                "tool": {
                    "tool_name": "x",
                    "input": {"token": "abc", "q": "hi"},
                },
            },
        ],
        "events": [],
    }
    out = redact_ingest_batch(batch, mode="default")
    assert out["runs"][0]["attributes"]["api_key"] == "[REDACTED]"
    assert out["runs"][0]["attributes"]["task"] == "ok"
    assert out["spans"][0]["llm"]["messages"][0]["content"] == "[REDACTED]"
    assert out["spans"][1]["tool"]["input"]["token"] == "[REDACTED]"


def test_api_key_scopes_enforce_ingest_vs_read(
    monkeypatch, tmp_path, hello_batch
) -> None:
    db_path = tmp_path / "scopes.db"
    monkeypatch.setenv("SENTINEL_DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("SENTINEL_AUTH_MODE", "api_key")
    monkeypatch.setenv("SENTINEL_API_KEYS", "k_ingest,k_read")
    monkeypatch.setenv("SENTINEL_API_KEY_SCOPES", "k_ingest:ingest,k_read:read")
    monkeypatch.setenv("SENTINEL_REDACTION_MODE", "off")
    from sentinel_server.config import get_settings

    get_settings.cache_clear()
    app = create_app(database_url=f"sqlite+pysqlite:///{db_path}")
    with TestClient(app) as client:
        denied = client.post("/v1/ingest", json=hello_batch, headers={"X-Sentinel-Api-Key": "k_read"})
        assert denied.status_code == 403

        ok = client.post(
            "/v1/ingest", json=hello_batch, headers={"X-Sentinel-Api-Key": "k_ingest"}
        )
        assert ok.status_code == 202, ok.text

        list_denied = client.get(
            "/v1/projects", headers={"X-Sentinel-Api-Key": "k_ingest"}
        )
        # ingest scope is included in READ_OK so ingest key can read — by design
        assert list_denied.status_code == 200

        read_ok = client.get(
            "/v1/projects", headers={"X-Sentinel-Api-Key": "k_read"}
        )
        assert read_ok.status_code == 200

        write_denied = client.post(
            "/v1/projects",
            json={"name": "Nope", "id": "proj_nope"},
            headers={"X-Sentinel-Api-Key": "k_read"},
        )
        assert write_denied.status_code == 403
    get_settings.cache_clear()


def test_ingest_applies_default_redaction(client: TestClient, hello_batch: dict) -> None:
    batch = deepcopy(hello_batch)
    batch["runs"][0]["attributes"] = {"api_key": "should-hide", "task": "demo"}
    # ensure llm message present
    for span in batch["spans"]:
        if span.get("kind") == "llm":
            span["llm"]["messages"] = [{"role": "user", "content": "secret prompt"}]
    assert client.post("/v1/ingest", json=batch).status_code == 202
    detail = client.get("/v1/projects/proj_demo/runs/run_hello_001").json()
    assert detail["run"]["attributes"]["api_key"] == "[REDACTED]"
    llm = next(s for s in detail["spans"] if s["kind"] == "llm")
    assert llm["llm"]["messages"][0]["content"] == "[REDACTED]"
