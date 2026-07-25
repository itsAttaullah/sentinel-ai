"""API tests for evaluation registry and scoring."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_smoke_evaluators(client: TestClient, project_id: str = "proj_demo") -> None:
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
            f"/v1/projects/{project_id}/evaluators",
            json={
                "evaluator_id": "used_search",
                "version": "1.0.0",
                "kind": "deterministic",
                "name": "Called web_search",
                "config": {"type": "tool_called", "tool_name": "web_search"},
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/v1/projects/{project_id}/evaluators",
            json={
                "evaluator_id": "task_judge",
                "version": "1.0.0",
                "kind": "judge",
                "name": "Task mentions Sentinel",
                "config": {
                    "mode": "stub",
                    "model": "gpt-judge-test",
                    "prompt_version": "task-v1",
                    "provider": "test",
                    "stub_passed": True,
                    "stub_score": 1.0,
                    "stub_rationale": "stub ok",
                },
            },
        ).status_code
        == 201
    )


def _create_suite(client: TestClient, project_id: str = "proj_demo") -> None:
    response = client.post(
        f"/v1/projects/{project_id}/suites",
        json={
            "suite_id": "smoke",
            "version": "1.0.0",
            "name": "Smoke suite",
            "definition": {
                "gate": "all_pass",
                "checks": [
                    {
                        "evaluator_id": "status_ok",
                        "evaluator_version": "1.0.0",
                    },
                    {
                        "evaluator_id": "used_search",
                        "evaluator_version": "1.0.0",
                    },
                    {
                        "evaluator_id": "task_judge",
                        "evaluator_version": "1.0.0",
                        "threshold": {"min_score": 0.5},
                    },
                ],
            },
        },
    )
    assert response.status_code == 201, response.text


def test_eval_suite_scores_run(client: TestClient, hello_batch: dict) -> None:
    assert client.post("/v1/ingest", json=hello_batch).status_code == 202
    _create_smoke_evaluators(client)
    _create_suite(client)

    # Versions are immutable
    again = client.post(
        "/v1/projects/proj_demo/evaluators",
        json={
            "evaluator_id": "status_ok",
            "version": "1.0.0",
            "kind": "deterministic",
            "name": "dup",
            "config": {"type": "run_status"},
        },
    )
    assert again.status_code == 400

    job = client.post(
        "/v1/projects/proj_demo/evals",
        json={"run_id": "run_hello_001", "suite_id": "smoke", "suite_version": "1.0.0"},
    )
    assert job.status_code == 202, job.text
    body = job.json()
    assert body["status"] == "succeeded"
    assert body["passed"] is True
    assert len(body["scores"]) == 3
    assert all(score["evaluator_version"] for score in body["scores"])
    judge = next(s for s in body["scores"] if s["evaluator_id"] == "task_judge")
    assert judge["evaluator_kind"] == "judge"
    assert judge["details"]["model"] == "gpt-judge-test"
    assert judge["details"]["prompt_version"] == "task-v1"

    fetched = client.get(f"/v1/projects/proj_demo/evals/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["passed"] is True

    scores = client.get("/v1/projects/proj_demo/runs/run_hello_001/scores")
    assert scores.status_code == 200
    assert len(scores.json()["items"]) == 3

    # Re-run creates new immutable score records
    job2 = client.post(
        "/v1/projects/proj_demo/evals",
        json={"run_id": "run_hello_001", "suite_id": "smoke"},
    )
    assert job2.status_code == 202
    assert job2.json()["id"] != body["id"]
    scores_again = client.get("/v1/projects/proj_demo/runs/run_hello_001/scores")
    assert len(scores_again.json()["items"]) == 6


def test_eval_fails_gate_when_check_fails(client: TestClient, hello_batch: dict) -> None:
    assert client.post("/v1/ingest", json=hello_batch).status_code == 202
    assert (
        client.post(
            "/v1/projects/proj_demo/evaluators",
            json={
                "evaluator_id": "no_retries",
                "version": "1.0.0",
                "kind": "deterministic",
                "name": "No retries",
                "config": {"type": "max_retries", "max": 0},
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/v1/projects/proj_demo/suites",
            json={
                "suite_id": "strict",
                "version": "1.0.0",
                "name": "Strict",
                "definition": {
                    "gate": "all_pass",
                    "checks": [
                        {"evaluator_id": "no_retries", "evaluator_version": "1.0.0"}
                    ],
                },
            },
        ).status_code
        == 201
    )
    job = client.post(
        "/v1/projects/proj_demo/evals",
        json={"run_id": "run_hello_001", "suite_id": "strict"},
    )
    assert job.status_code == 202
    assert job.json()["passed"] is False
