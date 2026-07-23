# Sentinel AI

**Observe. Measure. Benchmark. Improve.**

Sentinel AI is an open-source platform for evaluating, benchmarking, observing, and improving autonomous AI agents.

It is **not** an agent runtime. It is the measurement and observation layer that sits beside any agent framework—custom runtimes, ForgeMind, Research Agent, OpenAI Agents SDK, LangGraph, CrewAI, PydanticAI, and future frameworks via plugins.

---

## Why Sentinel AI Exists

Autonomous agents fail in ways that are hard to see: silent retries, expensive tool loops, planner regressions, memory strategy regressions, and model swaps that quietly raise latency and cost.

Teams need answers to questions such as:

- Why did an agent fail?
- Which model performs better?
- Which planner is more efficient?
- How many retries were needed?
- Which tools consume the most time?
- Which memory strategy performs best?
- What is the average latency?
- What is the execution cost?
- Which version of an agent regressed?

Sentinel AI turns agent execution into structured telemetry, reproducible benchmarks, comparable scores, and actionable diagnostics.

---

## What Sentinel AI Does

| Capability | Description |
|---|---|
| **Observe** | Capture traces, spans, tool calls, planner steps, memory ops, retries, and errors |
| **Measure** | Compute latency, cost, token usage, success rate, retry counts, and efficiency metrics |
| **Benchmark** | Run controlled suites across models, planners, tools, and agent versions |
| **Evaluate** | Score outcomes with rubrics, judges, and deterministic checks |
| **Visualize** | Explore timelines, flame-style traces, regressions, and leaderboards |
| **Compare** | Diff runs, versions, and configurations to find what changed |

---

## Non-Goals (v1)

- Building or hosting agents
- Replacing frameworks such as LangGraph or CrewAI
- Being a general LLM gateway (though adapters may record gateway traffic)
- Guaranteeing agent correctness without evaluation criteria defined by the user

---

## Documentation Map

| Document | Purpose |
|---|---|
| [ROADMAP.md](./ROADMAP.md) | Phased development plan |
| [docs/architecture/00-product-vision.md](./docs/architecture/00-product-vision.md) | Product vision |
| [docs/architecture/01-functional-requirements.md](./docs/architecture/01-functional-requirements.md) | Functional requirements |
| [docs/architecture/02-non-functional-requirements.md](./docs/architecture/02-non-functional-requirements.md) | Non-functional requirements |
| [docs/architecture/03-high-level-architecture.md](./docs/architecture/03-high-level-architecture.md) | System architecture |
| [docs/architecture/04-component-responsibilities.md](./docs/architecture/04-component-responsibilities.md) | Component ownership |
| [docs/architecture/05-data-flow.md](./docs/architecture/05-data-flow.md) | End-to-end data flows |
| [docs/architecture/06-technology-recommendations.md](./docs/architecture/06-technology-recommendations.md) | Stack recommendations |
| [docs/architecture/07-repository-structure.md](./docs/architecture/07-repository-structure.md) | Monorepo layout |
| [docs/architecture/08-risks-and-tradeoffs.md](./docs/architecture/08-risks-and-tradeoffs.md) | Risks and trade-offs |
| [docs/architecture/09-trace-schema-v1.md](./docs/architecture/09-trace-schema-v1.md) | Trace schema reference (v1) |
| [packages/schema/](./packages/schema/) | JSON Schema, fixtures, OpenAPI stubs |
| [packages/sdk-python/](./packages/sdk-python/) | Python instrumentation SDK |
| [apps/server/](./apps/server/) | Ingest API + Postgres control plane |
| [examples/hello-trace/](./examples/hello-trace/) | File-export quickstart |
| [docs/adr/](./docs/adr/) | Architecture Decision Records |
| [docs/diagrams/](./docs/diagrams/) | Mermaid architecture diagrams |
| [docs/phases/](./docs/phases/) | Per-phase scope notes |

---

## Status

**Phase 3 — Ingest & Store (complete on branch `feat/ingest-store`)**

- Schema: [`packages/schema`](./packages/schema/)
- Python SDK: [`packages/sdk-python`](./packages/sdk-python/)
- Server: [`apps/server`](./apps/server/)
- Example: [`examples/hello-trace`](./examples/hello-trace/)

### Quickstart (local stack)

```powershell
docker compose up --build
```

```powershell
pip install -e .\packages\sdk-python
python .\examples\hello-trace\main.py
```

Then POST a batch (or point `HttpExporter` at `http://localhost:8080/v1/ingest`).

---

## Suggested Contribution Workflow

1. Open a feature branch for a single roadmap phase
2. Implement only that phase’s scope
3. Update docs when architecture or behavior changes
4. Open a PR with the phase checklist completed

See [ROADMAP.md](./ROADMAP.md) for phase order and suggested branch names.

---

## License

License to be selected before the first public release (recommended candidates: Apache-2.0 or MIT). See [ADR-0005](./docs/adr/0005-license-and-open-source-posture.md).
