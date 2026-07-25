# Evaluation Model

**Status:** Active (Phase 7)  
**ADR:** [ADR-0006](../adr/0006-evaluation-model.md)  
**Implementation:** `apps/server/src/sentinel_server/services/evaluation.py`

---

## Principles

1. Every score references a **versioned evaluator** (`evaluator_id` + `version`).
2. Re-running an eval creates **new** score rows; history is never overwritten.
3. Suites bind checks → evaluators → optional thresholds → a gate (`all_pass` / `any_pass`).
4. Judges must record `model` + `prompt_version` (and optional provider/rubric).

---

## Entities

| Entity | Meaning |
|---|---|
| **Evaluator** | Immutable definition per `(project, evaluator_id, version)` |
| **Suite** | Immutable set of checks + gate per `(project, suite_id, version)` |
| **EvalJob** | One execution of a suite against a run |
| **Score** | Immutable result of one evaluator within a job |

---

## Deterministic types (`kind=deterministic`)

| `config.type` | Purpose |
|---|---|
| `run_status` | Expect `run.status` |
| `exact_match` | `path` equals `expected` |
| `regex` | `path` matches `pattern` |
| `tool_called` | Assert tool name appeared |
| `max_retries` | `metrics.retry_count` / retry events ≤ `max` |
| `max_wall_ms` | `metrics.wall_ms` ≤ `max_ms` |
| `json_schema_type` | Value at `path` has `expected_type` |

---

## Judge types (`kind=judge`)

Required: `model`, `prompt_version`.

| `mode` | Behavior |
|---|---|
| `heuristic` (default) | Rubric `checks` with `contains` / `equals` / `regex` |
| `stub` | Test helper using `stub_passed` / `stub_score` |

Live remote LLM HTTP judges are deferred; versioning fields are already required so CI can pin prompt/model identity.

---

## APIs

| Method | Path |
|---|---|
| POST/GET | `/v1/projects/{id}/evaluators` |
| GET | `/v1/projects/{id}/evaluators/{evaluator_id}` |
| POST/GET | `/v1/projects/{id}/suites` |
| GET | `/v1/projects/{id}/suites/{suite_id}` |
| POST | `/v1/projects/{id}/evals` |
| GET | `/v1/projects/{id}/evals/{job_id}` |
| GET | `/v1/projects/{id}/runs/{run_id}/scores` |

`POST .../evals` runs synchronously and returns `202` with the completed job + scores (status `succeeded` or `failed`).

---

## Example smoke flow

1. Ingest a run  
2. Register deterministic + judge evaluators (new versions only)  
3. Create suite `smoke@1.0.0` referencing those versions  
4. `POST /evals` with `{ run_id, suite_id }`  
5. Gate pass/fail from `job.passed`; inspect immutable `/scores`
