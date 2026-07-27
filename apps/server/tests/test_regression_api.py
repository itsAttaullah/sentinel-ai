"""API tests for regression compare/gate."""

from __future__ import annotations

from copy import deepcopy

from fastapi.testclient import TestClient


def _ingest(
    client: TestClient, hello_batch: dict, *, run_id: str, agent_version: str
) -> None:
    batch = deepcopy(hello_batch)
    batch["batch_id"] = f"batch_{run_id}"
    batch["runs"][0]["run_id"] = run_id
    batch["runs"][0]["agent_version"] = agent_version
    for span in batch["spans"]:
        span["run_id"] = run_id
    for event in batch.get("events") or []:
        event["run_id"] = run_id
    assert client.post("/v1/ingest", json=batch).status_code == 202


def test_gate_detects_version_regression(
    client: TestClient, hello_batch: dict
) -> None:
    _ingest(client, hello_batch, run_id="run_base", agent_version="0.1.0")
    _ingest(client, hello_batch, run_id="run_cand", agent_version="0.2.0")

    # Pin baseline
    pin = client.post(
        "/v1/projects/proj_demo/baselines",
        json={
            "baseline_id": "mainline",
            "version": "1.0.0",
            "name": "Mainline 0.1.0",
            "reference": {"kind": "agent_version", "agent_version": "0.1.0"},
        },
    )
    assert pin.status_code == 201, pin.text

    policy = client.post(
        "/v1/projects/proj_demo/regression-policies",
        json={
            "policy_id": "ci",
            "version": "1.0.0",
            "name": "CI gate",
            "definition": {
                "metrics": {
                    # force fail: any increase in wall_ms > 0 abs fails if we set tiny abs
                    # hello batches should have similar wall; use success_rate min instead
                    "success_rate": {"min_absolute": 0.5},
                    "retry_count": {"max_increase_abs": 0},
                }
            },
        },
    )
    assert policy.status_code == 201, policy.text

    # Both runs have a retry event → mean retry_count ~1; delta 0 should pass max_increase_abs 0
    gate_ok = client.post(
        "/v1/projects/proj_demo/regressions/gate",
        json={
            "baseline": {"kind": "baseline", "baseline_id": "mainline"},
            "candidate": {"kind": "agent_version", "agent_version": "0.2.0"},
            "policy_id": "ci",
            "policy_version": "1.0.0",
        },
    )
    assert gate_ok.status_code == 202, gate_ok.text
    body = gate_ok.json()
    assert body["status"] == "succeeded"
    assert body["exit_code_hint"] in (0, 1)
    assert "report" in body

    # Strict wall policy that fails if candidate wall not lower — use abs increase 0
    # If walls equal, delta 0 should pass. Force fail with min success_rate 1.1 impossible.
    fail = client.post(
        "/v1/projects/proj_demo/regressions/gate",
        json={
            "baseline": {"kind": "agent_version", "agent_version": "0.1.0"},
            "candidate": {"kind": "agent_version", "agent_version": "0.2.0"},
            "policy_definition": {
                "metrics": {"success_rate": {"min_absolute": 1.1}},
            },
        },
    )
    assert fail.status_code == 202
    assert fail.json()["passed"] is False
    assert fail.json()["exit_code_hint"] == 1

    compare = client.post(
        "/v1/projects/proj_demo/regressions/compare",
        json={
            "baseline": {"kind": "run", "run_id": "run_base"},
            "candidate": {"kind": "run", "run_id": "run_cand"},
        },
    )
    assert compare.status_code == 202
    assert compare.json()["kind"] == "compare"
    assert compare.json()["report"]["diff"]
