# Non-Functional Requirements

**Document:** Architecture Proposal — Non-Functional Requirements  
**Status:** Draft for Phase 0 (design baseline)

---

## 1. Performance

| ID | Requirement | Target (initial) |
|---|---|---|
| NFR-P01 | Ingest path must handle bursty agent traffic | ≥ 1k events/sec per single-node self-host (dev/staging class) |
| NFR-P02 | Run detail page loads for typical runs | p95 < 2s for runs with ≤ 2k spans |
| NFR-P03 | Metric aggregation for project dashboards | p95 < 5s for last 24h on single-node Postgres |
| NFR-P04 | SDK overhead on hot path | < 5% added wall time for typical tool/LLM spans (async export) |
| NFR-P05 | Batch ingest for CI suites | Support uploading multi-MB trace bundles |

Scaling beyond these targets is deferred to later phases (queueing, columnar analytics).

---

## 2. Reliability

| ID | Requirement |
|---|---|
| NFR-R01 | Ingest must be **at-least-once**; consumers must be idempotent on event IDs |
| NFR-R02 | SDK must buffer and retry on transient network failure |
| NFR-R03 | Control plane APIs must degrade gracefully when analytics is slow (serve raw traces first) |
| NFR-R04 | Schema validation failures must not crash the ingest worker; quarantine bad events |
| NFR-R05 | Document backup/restore for self-hosted deployments |

---

## 3. Scalability

| ID | Requirement |
|---|---|
| NFR-S01 | Architecture must allow horizontal scale of ingest and query independently |
| NFR-S02 | Storage design must support partitioning by project and time |
| NFR-S03 | Hot/cold separation: recent traces fast; older traces archived (object store) |
| NFR-S04 | Benchmark jobs must scale via worker pool (not the API process) |

---

## 4. Security & Privacy

| ID | Requirement |
|---|---|
| NFR-SEC01 | Secrets never logged (API keys, provider keys) |
| NFR-SEC02 | Configurable redaction for prompts, tool I/O, and user content |
| NFR-SEC03 | TLS for all remote transports in non-local profiles |
| NFR-SEC04 | Scoped API keys (ingest vs read vs admin) |
| NFR-SEC05 | Supply-chain hygiene: lockfiles, signed releases, minimal default permissions |
| NFR-SEC06 | Clear data residency story for self-hosted installs (data stays on user infra) |

---

## 5. Compatibility & Portability

| ID | Requirement |
|---|---|
| NFR-C01 | Canonical schema is language-agnostic (JSON Schema / protobuf later if needed) |
| NFR-C02 | First-class Python SDK; TypeScript SDK shortly after |
| NFR-C03 | Self-host via Docker Compose for local/dev |
| NFR-C04 | Cloud-agnostic: no hard dependency on a single cloud vendor |
| NFR-C05 | Adapters must pass a conformance test suite before “official” status |

---

## 6. Usability

| ID | Requirement |
|---|---|
| NFR-U01 | Time-to-first-trace ≤ 10 minutes with docs + hello-world sample |
| NFR-U02 | CLI ergonomics for common workflows (init, serve, query, eval) |
| NFR-U03 | Error messages must include remediation hints (schema/version mismatches) |
| NFR-U04 | Docs are a release artifact: architecture, ADRs, and phase notes stay current |

---

## 7. Maintainability

| ID | Requirement |
|---|---|
| NFR-M01 | Monorepo with clear package boundaries and public APIs |
| NFR-M02 | ADRs required for significant architectural changes |
| NFR-M03 | Adapter plugins isolated so framework churn does not break core |
| NFR-M04 | Automated unit/integration tests for schema, ingest, and evaluators |
| NFR-M05 | Semantic versioning for schema, SDKs, and server APIs |

---

## 8. Observability of Sentinel Itself

| ID | Requirement |
|---|---|
| NFR-O01 | Health endpoints for API and workers |
| NFR-O02 | Structured logs with request/run IDs |
| NFR-O03 | Metrics for ingest lag, queue depth, error rates |
| NFR-O04 | Optional OpenTelemetry export for Sentinel services |

---

## 9. Compliance Posture (Aspirational)

Not gating MVP, but design should not preclude:

- SOC2-oriented access controls for hosted offerings
- GDPR-style deletion of project data on request
- Audit logs of admin actions

---

## Related Documents

- [Functional Requirements](./01-functional-requirements.md)
- [Risks and Trade-offs](./08-risks-and-tradeoffs.md)
- [ADR-0002 Storage Strategy](../adr/0002-storage-strategy.md)
