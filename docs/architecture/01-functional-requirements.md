# Functional Requirements

**Document:** Architecture Proposal — Functional Requirements  
**Status:** Draft for Phase 0 (design baseline)  
**Priority legend:** P0 = MVP foundation · P1 = early product · P2 = scale / polish

---

## 1. Instrumentation & Ingestion

| ID | Requirement | Priority |
|---|---|---|
| FR-I01 | Provide language SDKs that emit agent execution events (start/end run, step, tool call, LLM call, memory op, retry, error) | P0 |
| FR-I02 | Define a stable, versioned **Agent Trace Schema** (canonical event + span model) | P0 |
| FR-I03 | Accept traces via HTTP API and optionally OTLP-compatible export paths | P0 |
| FR-I04 | Support offline / batch upload of traces for air-gapped or CI environments | P1 |
| FR-I05 | Provide framework adapters that map native lifecycle hooks to the schema | P1 |
| FR-I06 | Allow custom attributes and baggage without breaking schema validation | P0 |
| FR-I07 | Support correlation IDs across parent/child runs and multi-agent graphs | P0 |
| FR-I08 | Redact or hash sensitive fields via configurable PII policies at ingest | P1 |

---

## 2. Trace Storage & Query

| ID | Requirement | Priority |
|---|---|---|
| FR-T01 | Persist runs, spans, events, and attachments with durable IDs | P0 |
| FR-T02 | Query runs by project, agent version, time range, status, tags | P0 |
| FR-T03 | Retrieve a full run timeline (ordered spans + events) | P0 |
| FR-T04 | Support pagination and filtering for large projects | P1 |
| FR-T05 | Retain raw payloads (prompts/tool I/O) under retention policies | P1 |
| FR-T06 | Export runs as JSON / Parquet for offline analysis | P1 |

---

## 3. Metrics & Attribution

| ID | Requirement | Priority |
|---|---|---|
| FR-M01 | Compute per-run latency (wall clock, critical path) | P0 |
| FR-M02 | Aggregate token usage and estimated cost by model and provider | P0 |
| FR-M03 | Count retries, tool failures, and error classes | P0 |
| FR-M04 | Attribute time to tools, LLM calls, planner steps, and memory ops | P0 |
| FR-M05 | Project-level dashboards: success rate, p50/p95 latency, cost | P1 |
| FR-M06 | Configurable pricing tables for cost estimation | P1 |

---

## 4. Evaluation

| ID | Requirement | Priority |
|---|---|---|
| FR-E01 | Attach evaluation criteria to datasets / suites (pass/fail checks) | P1 |
| FR-E02 | Support deterministic evaluators (exact match, regex, JSON schema, tool-call assertions) | P1 |
| FR-E03 | Support LLM-as-judge evaluators with versioned prompts/rubrics | P1 |
| FR-E04 | Store scores, rationales, and evaluator versions per run | P1 |
| FR-E05 | Aggregate suite scores and produce pass/fail gates | P1 |
| FR-E06 | Allow human review / override of scores | P2 |

---

## 5. Benchmarking

| ID | Requirement | Priority |
|---|---|---|
| FR-B01 | Define benchmark suites: fixed tasks + expected outcomes + configs | P1 |
| FR-B02 | Sweep dimensions: model, planner, tools, memory strategy, agent version | P1 |
| FR-B03 | Record environment fingerprints (SDK versions, adapter versions, seeds) | P1 |
| FR-B04 | Produce leaderboards and pairwise comparisons | P2 |
| FR-B05 | Detect statistically significant regressions between baselines | P2 |

---

## 6. Visualization & UX

| ID | Requirement | Priority |
|---|---|---|
| FR-U01 | Web UI for projects, runs list, and run detail timeline | P1 |
| FR-U02 | Span waterfall / flame-style view of a run | P1 |
| FR-U03 | Cost and latency breakdown charts | P1 |
| FR-U04 | Diff view between two runs or two agent versions | P2 |
| FR-U05 | CLI for init, ingest, query, eval, and report | P0 |
| FR-U06 | Public REST/JSON API for automation | P0 |

---

## 7. Versioning & Regression

| ID | Requirement | Priority |
|---|---|---|
| FR-V01 | Tag runs with `agent_version`, `config_hash`, and git SHA (optional) | P0 |
| FR-V02 | Compare metrics and scores across versions | P1 |
| FR-V03 | CI mode: fail build when regressions exceed thresholds | P2 |
| FR-V04 | Baseline pinning for protected branches / releases | P2 |

---

## 8. Multi-Framework Support

| ID | Requirement | Priority |
|---|---|---|
| FR-F01 | Plugin interface for framework adapters (discoverable packages) | P1 |
| FR-F02 | Official adapters roadmap: custom SDK first, then popular frameworks | P1 |
| FR-F03 | Adapter conformance tests against the canonical schema | P1 |
| FR-F04 | Document mapping guides for community adapters | P1 |

**Target frameworks (adapters, not core dependencies):**

- Custom agent runtimes (native SDK)
- ForgeMind
- Research Agent
- OpenAI Agents SDK
- LangGraph
- CrewAI
- PydanticAI
- Future frameworks via plugins

---

## 9. Projects, Auth & Tenancy (Self-Hosted First)

| ID | Requirement | Priority |
|---|---|---|
| FR-A01 | Organize data by **Project** (and optional Environments) | P0 |
| FR-A02 | API keys for ingest and read scopes | P1 |
| FR-A03 | Local single-user mode with no auth (dev default) | P0 |
| FR-A04 | Optional multi-user RBAC for self-hosted teams | P2 |

---

## 10. Extensibility

| ID | Requirement | Priority |
|---|---|---|
| FR-X01 | Webhooks on run completion / eval failure | P2 |
| FR-X02 | Pluggable storage backends (local FS → Postgres → object store) | P1 |
| FR-X03 | Custom metric extractors and evaluators as plugins | P2 |
| FR-X04 | OpenAPI-documented HTTP API | P0 |

---

## Explicit Non-Requirements

| ID | Non-requirement |
|---|---|
| NR-01 | Executing or scheduling agents inside Sentinel |
| NR-02 | Replacing framework-native debugging UIs entirely on day one |
| NR-03 | Training models or managing model weights |
| NR-04 | Guaranteeing factual correctness without user-defined evaluators |

---

## Related Documents

- [Non-Functional Requirements](./02-non-functional-requirements.md)
- [Component Responsibilities](./04-component-responsibilities.md)
