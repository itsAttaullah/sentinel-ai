# Sentinel AI Roadmap

Phased delivery plan. **One phase = one feature branch.** Do not implement future phases ahead of schedule.

See also: [phase dependency diagram](./docs/diagrams/05-roadmap-phases.md) · [docs/phases/](./docs/phases/)

---

## Phase Overview

| Phase | Name | Goal | Suggested branch |
|---|---|---|---|
| **0** | Architecture & Foundations | Design-only proposal, ADRs, diagrams | `docs/architecture` |
| **1** | Schema & Contracts | Versioned canonical trace schema + OpenAPI stubs | `feat/schema-contracts` |
| **2** | Python SDK | Instrumentation SDK + hello-trace example | `feat/python-sdk` |
| **3** | Ingest & Store | API ingest, Postgres persistence, Compose | `feat/ingest-store` |
| **4** | Metrics Engine | Latency, cost, retries, tool attribution | `feat/metrics-engine` |
| **5** | CLI & Developer Experience | CLI workflows for init/serve/query/upload | `feat/cli-dx` |
| **6** | Web UI Foundations | Projects, run list, timeline waterfall | `feat/web-ui` |
| **7** | Evaluation Engine | Deterministic + judge evaluators, scores | `feat/evaluation` |
| **8** | Benchmarking | Suites, config matrix, comparisons | `feat/benchmarking` |
| **9** | Framework Adapters | Plugin interface + first official adapters | `feat/adapters` |
| **10** | Regression & CI Gates | Version diffs, thresholds, CI reports | `feat/regression-ci` |
| **11** | Hardening & OSS Launch | Security, docs polish, release readiness | `feat/hardening-oss` |

---

## Phase Summaries

### Phase 0 — Architecture & Foundations *(current)*

Produce product vision, requirements, HLD, ADRs, diagrams, repo plan, and this roadmap. **No business logic code.**

### Phase 1 — Schema & Contracts *(complete)*

Publish JSON Schema for runs/spans/events; define compatibility policy; stub OpenAPI for ingest/control plane; golden fixtures.

### Phase 2 — Python SDK *(complete)*

Implement tracer APIs, context propagation, async export client (can target mock/file sink before live server), hello-trace example.

### Phase 3 — Ingest & Store

FastAPI ingest + project APIs; Postgres models; idempotent upserts; Docker Compose; quarantine for invalid batches.

### Phase 4 — Metrics Engine

Derive per-run and rollup metrics: latency, tokens, estimated cost, retries, tool/LLM time share.

### Phase 5 — CLI & Developer Experience

`sentinel` CLI: init, serve helpers, upload, query, whoami; improve time-to-first-trace docs.

### Phase 6 — Web UI Foundations

Project switcher, run list filters, run detail timeline/waterfall, basic metric panels.

### Phase 7 — Evaluation Engine

Suite/evaluator registry; deterministic checks; optional LLM judge; immutable versioned scores.

### Phase 8 — Benchmarking

Benchmark suite definitions; config matrix metadata; aggregation; pairwise comparison views/reports.

### Phase 9 — Framework Adapters

Adapter plugin interface + conformance suite; ship first adapters (priority: custom reference, then highest-demand frameworks from the vision list).

### Phase 10 — Regression & CI Gates

Cross-version diffs; threshold policies; CI-friendly reports and exit codes; baseline pinning.

### Phase 11 — Hardening & OSS Launch

Redaction defaults, auth scopes, backup docs, performance pass, CONTRIBUTING, license finalization, release tagging process (executed by maintainers).

---

## Out of Roadmap (Future Backlog)

- TypeScript SDK (can pull forward after Phase 2 if needed)
- Hosted multi-tenant SaaS
- ClickHouse/DuckDB analytics tier
- Full OIDC SSO
- Auto-healing / agent rewriting
- Marketplace UI for community adapters

---

## Working Agreement

1. Update `docs/phases/phase-XX-*.md` when a phase starts/finishes.  
2. Update ADRs when decisions change.  
3. No Git operations by the coding agent unless the human explicitly requests them.  
4. Human owns branches, commits, merges, and pushes.
