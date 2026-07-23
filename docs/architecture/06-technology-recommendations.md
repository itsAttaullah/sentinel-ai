# Technology Recommendations

**Document:** Architecture Proposal — Technology Choices  
**Status:** Recommendations (not yet implemented)  
**Related ADRs:** 0002, 0003, 0004

---

## 1. Guiding Constraints

1. Self-hostable with Docker Compose on a developer laptop  
2. Strong Python ecosystem (agents are predominantly Python today)  
3. Schema and API stability over exotic infrastructure  
4. Avoid premature multi-cloud complexity  
5. Prefer boring, proven technology for the control plane

---

## 2. Recommended Stack (MVP → Early Product)

| Concern | Recommendation | Rationale |
|---|---|---|
| **Canonical schema** | JSON Schema (draft 2020-12) + versioned JSON events | Universal, easy to validate in any language |
| **Primary SDK language** | Python 3.11+ | Agent ecosystem gravity |
| **Secondary SDK** | TypeScript (Node 20+) | Web agents, JS tooling, UI adjacency |
| **API server** | Python (FastAPI) | Fast iteration, OpenAPI free, async-friendly |
| **Workers** | Same codebase, ARQ or Celery / NATS consumers | Keep one language for server-side early on |
| **Queue** | Redis (MVP) → NATS/JetStream later if needed | Simple Compose story |
| **Primary DB** | PostgreSQL 16 | Relational integrity for projects/runs/scores |
| **Object store** | Filesystem (dev) / MinIO or S3-compatible (deployed) | Large payloads |
| **UI** | TypeScript + Next.js (or Vite + React) | Strong DX; pick one and stick to it |
| **CLI** | Python (`typer` / `click`) sharing server client libs | One CLI for ingest/eval/report |
| **Charts / timeline** | React + a lean chart lib; custom waterfall for spans | Domain-specific UX matters |
| **Auth (dev)** | None / local mode | Frictionless hello-world |
| **Auth (team)** | API keys first; OIDC later | Matches observability tools |
| **Packaging** | pnpm/npm workspaces + uv/poetry for Python in a monorepo | Clear boundaries |
| **Containers** | Docker + Compose | Universal local path |
| **CI** | GitHub Actions (when remote enabled by maintainers) | Standard OSS |

---

## 3. Optional / Later Technologies

| Concern | Candidate | When |
|---|---|---|
| Columnar analytics | DuckDB / ClickHouse / Parquet lake | When dashboard aggregations outgrow Postgres |
| Protobuf / gRPC | Secondary wire format | When JSON ingest CPU becomes a bottleneck |
| OpenTelemetry | OTLP ingest bridge | For teams standardized on OTel |
| Feature flags | Simple config flags | Multi-tenant hosted era |
| Search | OpenSearch / pgvector | Full-text over prompts; semantic search over runs |

---

## 4. Explicit Non-Choices (For Now)

| Avoid early | Why |
|---|---|
| Kubernetes-first deployment | Too heavy for MVP; support later via community charts |
| Microservices explosion | Start modular monolith + workers |
| Kafka | Operational cost unjustified until volume demands it |
| Multi-region active-active | Out of scope for early phases |
| Embedding a specific agent framework in core | Violates product principles |

---

## 5. Schema & Contract Tooling

- JSON Schema as source of truth for events/spans  
- Codegen or shared validators in Python and TypeScript  
- OpenAPI 3 for HTTP control plane  
- Compatibility policy: additive changes preferred; breaking changes require major `schema_version`

---

## 6. Testing Technology

| Layer | Approach |
|---|---|
| Unit | pytest / vitest |
| Contract | Schema fixtures + golden JSON |
| Integration | Compose-based tests (API + Postgres) |
| Adapter conformance | Shared test vectors in `packages/conformance` |
| Eval smoke | Deterministic evaluators only in CI (no flaky judges) |

---

## 7. Decision Summary

**MVP stack:** FastAPI + Postgres + Redis + Python SDK + React UI + Docker Compose.

This maximizes speed-to-first-trace while leaving room for OTLP, columnar analytics, and multi-language SDKs.

---

## Related Documents

- [ADR-0002 Storage Strategy](../adr/0002-storage-strategy.md)
- [ADR-0003 Modular Monolith](../adr/0003-modular-monolith.md)
- [ADR-0004 SDK-First Instrumentation](../adr/0004-sdk-first-instrumentation.md)
- [Repository Structure](./07-repository-structure.md)
