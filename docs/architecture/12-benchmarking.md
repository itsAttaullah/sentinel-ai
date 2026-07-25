# Benchmarking Model

**Status:** Active (Phase 8)  
**Implementation:** `apps/server/src/sentinel_server/services/benchmarking.py`

---

## Boundary

Sentinel **does not execute agents**. Callers run configurations externally, ingest traces, then register matrix cells. Sentinel aggregates scores/metrics and produces comparisons.

---

## Entities

| Entity | Meaning |
|---|---|
| **BenchmarkSuite** | Versioned definition: tasks, optional eval suite, sweep dimensions |
| **BenchmarkCell** | One matrix cell: dimensions + run + fingerprint (+ optional scores) |
| **BenchmarkJob** | Immutable comparison report snapshot over cells |

---

## Dimensions (FR-B02)

Default sweep keys: `model`, `planner`, `tools`, `memory`, `agent_version`.  
Cells may supply any dimension map; leaderboard groups by the normalized key.

---

## Environment fingerprint (FR-B03)

Captured on each cell from the run + optional overrides:

- `schema_version`, `agent_name`, `agent_version`
- `sdk_version`, `adapter_version`, `config_hash`, `git_sha`, `seed`
- `sentinel_server_version`, `python_version`, `platform`

---

## Comparison (FR-B04)

- **Leaderboard:** pass rate, mean score, mean wall/cost, ranked by pass → score → latency  
- **Pairwise:** deltas vs `baseline_agent_version` when provided  

Statistical significance helpers remain deferred (Phase 10 / ADR-0006 follow-up).

---

## APIs

| Method | Path |
|---|---|
| POST/GET | `/v1/projects/{id}/benchmark-suites` |
| POST/GET | `/v1/projects/{id}/benchmark-suites/{benchmark_id}/cells` |
| GET | `/v1/projects/{id}/benchmark-suites/{benchmark_id}/leaderboard` |
| POST | `/v1/projects/{id}/benchmarks` |
| GET | `/v1/projects/{id}/benchmarks/{job_id}` |

`POST .../benchmarks` accepts `suite_id` (alias) or `benchmark_id`.
