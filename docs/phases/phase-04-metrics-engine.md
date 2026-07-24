# Phase 4 — Metrics Engine

| Field | Value |
|---|---|
| **Status** | Complete |
| **Branch** | `feat/metrics-engine` |
| **Depends on** | Phase 3 |

## Objectives

- Derive latency, token, cost estimates, retry counts  
- Attribute time to tool/LLM/planner/memory spans  
- Project-level aggregate endpoints  

## In Scope (delivered)

- Metrics derivation on ingest (+ explicit recompute)
- `RunMetrics` persistence
- Pricing table (`apps/server/pricing/default.json`) + `SENTINEL_PRICING_PATH`
- Run detail `metrics`, run list `metrics_summary`
- `GET /v1/projects/{id}/metrics`
- Unit + API tests
- Architecture doc `10-metrics-and-pricing.md`

## Out of Scope

- Subjective quality scores (Phase 7)  
- Full dashboard polish (Phase 6 can consume APIs)  
- Separate async worker process (derivation runs in-request after ingest; same code path is worker-ready)

## Exit Criteria

- [x] Metrics present on run detail API  
- [x] Pricing table mechanism documented  
- [x] Worker path covered by tests  

## Suggested Commit Message

```text
feat: derive run metrics for latency, cost, and attribution
```

## Suggested PR Title

`feat: run metrics for latency, cost, and attribution`

## Manual Testing Checklist

- [ ] `pip install -e ".\apps\server[dev]"`
- [ ] `pytest .\apps\server\tests -q`
- [ ] Ingest hello batch → GET run detail includes `metrics.wall_ms` / tokens / retries
- [ ] GET `/v1/projects/proj_demo/metrics` returns aggregates
- [ ] Override `SENTINEL_PRICING_PATH` and recompute a run
