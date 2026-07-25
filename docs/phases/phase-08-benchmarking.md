# Phase 8 — Benchmarking

| Field | Value |
|---|---|
| **Status** | Complete |
| **Branch** | `feat/benchmarking` |
| **Depends on** | Phase 7 |

## Objectives

- Benchmark suite + config matrix metadata  
- Aggregation across cells (model/planner/memory/version)  
- Comparison reports / leaderboard views  

## Boundary Reminder

Sentinel does not execute agents; callers run configurations while Sentinel records and scores.

## In Scope (delivered)

- Models: `BenchmarkSuite`, `BenchmarkCell`, `BenchmarkJob`
- Environment fingerprints on cells
- Cell registration with optional `run_eval`
- Leaderboard + pairwise deltas vs baseline agent version
- Light web leaderboard page
- `examples/benchmark-smoke/`
- Docs + OpenAPI + tests

## Out of Scope

- Agent execution / orchestration  
- Statistical significance gates (Phase 10)  
- Full visual matrix designer UI  

## Exit Criteria

- [x] Matrix comparison available via API (and UI if Phase 6 present)  
- [x] Environment fingerprint captured  

## Suggested Commit Message

```text
feat: add benchmarking suites and configuration comparisons
```

## Suggested PR Title

`feat: benchmarking suites and configuration comparisons`

## Manual Testing Checklist

- [ ] `pytest .\apps\server\tests\test_fingerprint.py .\apps\server\tests\test_benchmarking_api.py -q`
- [ ] Register benchmark suite + two cells with different `agent_version`
- [ ] `GET .../leaderboard?baseline_agent_version=0.1.0` shows ranks + pairwise
- [ ] `POST /benchmarks` returns succeeded job with report
- [ ] Open `/projects/proj_demo/benchmarks/smoke_bench` in the web UI
