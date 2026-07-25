"""API tests for benchmarking suites, cells, and comparisons."""

from __future__ import annotations

from copy import deepcopy

from fastapi.testclient import TestClient


def _setup_eval_suite(client: TestClient, project_id: str = "proj_demo") -> None:
    assert (
        client.post(
            f"/v1/projects/{project_id}/evaluators",
            json={
                "evaluator_id": "status_ok",
                "version": "1.0.0",
                "kind": "deterministic",
                "name": "Run succeeded",
                "config": {"type": "run_status", "expected": "succeeded"},
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/v1/projects/{project_id}/suites",
            json={
                "suite_id": "smoke_eval",
                "version": "1.0.0",
                "name": "Smoke eval",
                "definition": {
                    "gate": "all_pass",
                    "checks": [
                        {"evaluator_id": "status_ok", "evaluator_version": "1.0.0"}
                    ],
                },
            },
        ).status_code
        == 201
    )


def _ingest_variant(
    client: TestClient, hello_batch: dict, *, run_id: str, agent_version: str, model: str
) -> None:
    batch = deepcopy(hello_batch)
    batch["batch_id"] = f"batch_{run_id}"
    run = batch["runs"][0]
    run["run_id"] = run_id
    run["agent_version"] = agent_version
    run["attributes"] = {"model": model, "planner": "react", "memory": "none", "seed": 7}
    for span in batch["spans"]:
        span["run_id"] = run_id
        if span.get("kind") == "llm":
            span["llm"] = {**(span.get("llm") or {}), "model": model}
    for event in batch.get("events") or []:
        event["run_id"] = run_id
    assert client.post("/v1/ingest", json=batch).status_code == 202


def test_benchmark_matrix_comparison(client: TestClient, hello_batch: dict) -> None:
    _setup_eval_suite(client)
    _ingest_variant(
        client, hello_batch, run_id="run_a", agent_version="0.1.0", model="gpt-a"
    )
    _ingest_variant(
        client, hello_batch, run_id="run_b", agent_version="0.2.0", model="gpt-b"
    )

    created = client.post(
        "/v1/projects/proj_demo/benchmark-suites",
        json={
            "benchmark_id": "smoke_bench",
            "version": "1.0.0",
            "name": "Smoke benchmark",
            "definition": {
                "eval_suite_id": "smoke_eval",
                "eval_suite_version": "1.0.0",
                "tasks": [{"task_id": "hello", "description": "Hello smoke task"}],
                "dimensions": ["model", "planner", "memory", "agent_version"],
            },
        },
    )
    assert created.status_code == 201, created.text

    for run_id, version, model in (
        ("run_a", "0.1.0", "gpt-a"),
        ("run_b", "0.2.0", "gpt-b"),
    ):
        cell = client.post(
            "/v1/projects/proj_demo/benchmark-suites/smoke_bench/cells",
            json={
                "task_id": "hello",
                "run_id": run_id,
                "run_eval": True,
                "dimensions": {
                    "agent_version": version,
                    "model": model,
                    "planner": "react",
                    "memory": "none",
                },
                "environment": {"adapter_version": "custom-0.1"},
            },
        )
        assert cell.status_code == 201, cell.text
        body = cell.json()
        assert body["environment_fingerprint"]["adapter_version"] == "custom-0.1"
        assert body["environment_fingerprint"]["agent_version"] == version
        assert body["scores_summary"]["passed"] is True

    board = client.get(
        "/v1/projects/proj_demo/benchmark-suites/smoke_bench/leaderboard",
        params={"baseline_agent_version": "0.1.0"},
    )
    assert board.status_code == 200, board.text
    report = board.json()
    assert report["cell_count"] == 2
    assert report["group_count"] == 2
    assert len(report["leaderboard"]) == 2
    assert "environment_fingerprint" not in report  # fingerprints live on cells / rows
    assert report["leaderboard"][0]["fingerprints"]

    job = client.post(
        "/v1/projects/proj_demo/benchmarks",
        json={
            "suite_id": "smoke_bench",
            "baseline_agent_version": "0.1.0",
        },
    )
    assert job.status_code == 202, job.text
    assert job.json()["status"] == "succeeded"
    assert job.json()["report"]["group_count"] == 2

    fetched = client.get(f"/v1/projects/proj_demo/benchmarks/{job.json()['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["report"]["pairwise"]
