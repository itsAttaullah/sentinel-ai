# Metrics & Pricing

**Status:** Active (Phase 4)  
**Implementation:** `apps/server/src/sentinel_server/services/metrics.py`

---

## 1. What is derived

After each successful ingest (and on explicit recompute), Sentinel computes per-run metrics:

| Metric | Source |
|---|---|
| `wall_ms` | Run `ended_at - started_at` |
| `attribution_ms` | Sum of span durations by `kind` |
| `attribution_share` | Share of `span_total_ms` per kind |
| `tokens` | Sum of LLM span `tokens_in` / `tokens_out` |
| `estimated_cost_usd` | Tokens × pricing table rates |
| `cost_by_model` | Cost rollup by `provider:model` |
| `retry_count` | Count of events with `type=retry` |
| `error_event_count` | Count of events with `type=error` |
| `span_counts` / `span_error_count` | Span tallies |

**Note:** `attribution_ms` sums span wall times. Overlapping spans can double-count; this is intentional for v1 tool/LLM time share, not a critical-path exclusive timeline.

---

## 2. APIs

| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/projects/{project_id}/runs/{run_id}` | Includes `metrics` by default |
| GET | `/v1/projects/{project_id}/runs` | Includes `metrics_summary` per run |
| GET | `/v1/projects/{project_id}/metrics` | Project aggregates (avg/p50/p95, cost, retries) |
| POST | `/v1/projects/{project_id}/runs/{run_id}/metrics/recompute` | Rebuild metrics from stored traces |

---

## 3. Pricing table

Default file: [`apps/server/pricing/default.json`](../../apps/server/pricing/default.json)

Override:

```powershell
$env:SENTINEL_PRICING_PATH = "C:\path\to\my-pricing.json"
```

Schema:

```json
{
  "version": "2026-07-24",
  "currency": "USD",
  "models": {
    "openai:gpt-4.1-mini": { "input_per_1m": 0.4, "output_per_1m": 1.6 },
    "*": { "input_per_1m": 1.0, "output_per_1m": 3.0 }
  }
}
```

Keys are `{provider}:{model}` (lowercase). Unknown models fall back to `*`.

Costs are **estimates** for comparison — not invoices.

---

## Related

- [Functional requirements — Metrics](./01-functional-requirements.md)
- [ADR-0002 Storage](../adr/0002-storage-strategy.md)
