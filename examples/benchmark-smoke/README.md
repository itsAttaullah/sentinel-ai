# Benchmark smoke example

Tiny end-to-end sketch: ingest runs → eval suite → benchmark suite → cells → leaderboard.

Assumes API at `http://localhost:8080` and local auth.

## 1. Ingest two configs

Use `packages/schema/fixtures/valid/ingest-batch.hello.json` twice with distinct `run_id` / `agent_version` / `attributes.model` (see server tests for the shape).

## 2. Register eval suite

```http
POST /v1/projects/proj_demo/evaluators
POST /v1/projects/proj_demo/suites
```

Deterministic `run_status` check is enough for smoke.

## 3. Register benchmark suite

```json
{
  "benchmark_id": "smoke_bench",
  "version": "1.0.0",
  "name": "Smoke benchmark",
  "definition": {
    "eval_suite_id": "smoke_eval",
    "eval_suite_version": "1.0.0",
    "tasks": [{"task_id": "hello", "description": "Hello smoke task"}],
    "dimensions": ["model", "planner", "memory", "agent_version"]
  }
}
```

## 4. Attach cells

```json
{
  "task_id": "hello",
  "run_id": "run_a",
  "run_eval": true,
  "dimensions": {
    "agent_version": "0.1.0",
    "model": "gpt-a",
    "planner": "react",
    "memory": "none"
  },
  "environment": {"adapter_version": "custom-0.1"}
}
```

## 5. Compare

```http
GET /v1/projects/proj_demo/benchmark-suites/smoke_bench/leaderboard?baseline_agent_version=0.1.0
POST /v1/projects/proj_demo/benchmarks
{"suite_id":"smoke_bench","baseline_agent_version":"0.1.0"}
```

Sentinel records and scores; it does not run the agent configurations.
