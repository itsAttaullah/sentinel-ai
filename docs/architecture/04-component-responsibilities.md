# Component Responsibilities

**Document:** Architecture Proposal — Component Map  
**Status:** Draft for Phase 0

---

## 1. Responsibility Matrix

| Component | Owns | Does not own |
|---|---|---|
| **SDK (Python/TS)** | Instrumentation API, buffering, export, local context propagation | Persistence, evaluation logic, UI |
| **Framework Adapters** | Mapping framework hooks → SDK spans/events | Canonical schema evolution |
| **Ingest Gateway** | Auth, rate limits, schema validation, enqueue | Long-running analytics |
| **Control Plane API** | CRUD for projects, query runs, trigger evals/benchmarks | Agent execution |
| **Trace Store** | Durable runs/spans/events/metadata | Large binary blobs (prefer object store) |
| **Object Store** | Prompt dumps, artifacts, batch uploads | Relational queries |
| **Metrics Engine** | Derived latency/cost/retry/tool attribution | Subjective quality scores |
| **Evaluation Engine** | Running evaluators, storing scores | Deciding which tasks exist |
| **Benchmark Orchestrator** | Suite definitions, sweeps, comparison jobs | Running the agent (caller runs agent; Sentinel records) |
| **Workers** | Async processing pipelines | Synchronous user UX |
| **Web UI** | Visualization and exploration | Source of truth (API is) |
| **CLI** | Developer workflows and CI helpers | Business rules beyond API client |
| **Conformance Suite** | Adapter compliance tests | Product features |

---

## 2. Component Deep Dive

### 2.1 Sentinel SDK

**Purpose:** Minimal, ergonomic instrumentation for agent authors.

**Responsibilities:**

- Create/end runs and spans
- Record LLM/tool/memory/planner semantics
- Attach tags, versions, baggage
- Async batch export with retry
- Context propagation across async tasks / threads where supported

**Public concepts (illustrative):**

```text
tracer.start_run(...)
span = tracer.start_span(kind="tool" | "llm" | "planner" | "memory" | ...)
span.end()
tracer.record_event(...)
tracer.end_run(...)
```

---

### 2.2 Framework Adapters

**Purpose:** Zero/low-touch instrumentation for popular runtimes.

**Responsibilities:**

- Subscribe to framework callbacks / middleware
- Translate to SDK calls
- Preserve correlation across graph nodes / crew members
- Declare supported framework versions

**Packaging:** Separate packages, e.g. `@sentinel-ai/adapter-langgraph`, `sentinel-adapter-crewai`.

---

### 2.3 Ingest Gateway

**Purpose:** Reliable front door for telemetry.

**Responsibilities:**

- Authenticate ingest keys
- Validate against schema version
- Normalize legacy minor versions when compatible
- Enqueue accepted batches
- Quarantine invalid payloads with actionable errors

---

### 2.4 Control Plane API

**Purpose:** System of record for configuration and query.

**Responsibilities:**

- Projects, environments, API keys
- Run search and detail
- Dataset/suite/evaluator registration
- Trigger evaluation and benchmark jobs
- Export endpoints

---

### 2.5 Persistence

| Store | Data |
|---|---|
| **Relational (Postgres)** | Projects, runs index, span metadata, scores, suites |
| **Object store** | Large payloads, attachments, Parquet exports |
| **Cache / queue** | Job queues, short-lived aggregates |

---

### 2.6 Metrics Engine

**Purpose:** Turn traces into numbers teams can act on.

**Derived metrics (initial set):**

- Wall-clock duration, critical-path duration
- Token in/out, estimated cost
- Retry count, error count by class
- Tool latency share, LLM latency share
- Success/failure (status + optional eval gate)

---

### 2.7 Evaluation Engine

**Purpose:** Score runs against explicit criteria.

**Evaluator types:**

1. **Deterministic** — exact/regex/JSON schema/assertions on tool calls  
2. **Model judge** — rubric + LLM scoring (versioned)  
3. **Custom plugin** — user-provided scorer  

**Outputs:** score value(s), pass/fail, rationale, evaluator version, timestamps.

---

### 2.8 Benchmark Orchestrator

**Purpose:** Compare configurations reproducibly.

**Important boundary:** Sentinel does **not** execute the agent.  
Callers (CI scripts, harnesses) execute agents under different configs while Sentinel records and scores. The orchestrator coordinates **suite definitions, expected matrices, aggregation, and comparison**—optionally invoking user-provided runner hooks later.

---

### 2.9 Experience Layer

| Surface | Primary users | Jobs |
|---|---|---|
| Web UI | Engineers, eval teams | Explore, debug, compare |
| CLI | Developers, CI | Init, serve, query, eval, report |
| HTTP API | Integrators | Automation |
| Reports | PR / CI | Pass-fail + summaries |

---

## 3. Package Boundary Rules

1. `schema` has no dependency on frameworks or UI.  
2. `sdk` depends on `schema` only (plus minimal HTTP client).  
3. `adapters/*` depend on `sdk` + one framework.  
4. `server` depends on `schema`, never on adapters.  
5. `ui` talks only to public API contracts.  
6. Circular dependencies are forbidden.

---

## Related Documents

- [High-Level Architecture](./03-high-level-architecture.md)
- [Repository Structure](./07-repository-structure.md)
- [Component Diagram](../diagrams/02-component-diagram.md)
