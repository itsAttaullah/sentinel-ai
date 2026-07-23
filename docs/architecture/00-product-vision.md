# Product Vision

**Document:** Architecture Proposal — Product Vision  
**Status:** Accepted for Phase 0  
**Audience:** Maintainers, contributors, early adopters

---

## 1. Elevator Pitch

Sentinel AI is the **observability and evaluation platform for autonomous agents**.  
Where APM tools watch microservices, Sentinel AI watches planners, tools, memory, retries, models, and outcomes—so teams can measure, compare, and improve agents without owning the agent runtime.

---

## 2. Problem Statement

Agent systems are becoming production software, but their failure modes are opaque:

1. **Opaque execution** — Multi-step planners, tool loops, and memory updates leave little structured evidence.
2. **Weak comparability** — “It worked better with GPT-X” is anecdote, not a reproducible benchmark.
3. **Hidden cost** — Token usage, tool latency, and retry storms dominate spend without attribution.
4. **Silent regressions** — Prompt, planner, or model changes break quality without CI-visible signals.
5. **Framework fragmentation** — Each runtime (LangGraph, CrewAI, custom, etc.) invents its own logs.

Teams need a **framework-agnostic measurement layer**, not another agent framework.

---

## 3. Vision Statement

> Sentinel AI becomes the open standard for capturing agent execution as structured traces, scoring those traces against explicit criteria, benchmarking configurations at scale, and surfacing regressions before they reach users.

In five years, “instrumented with Sentinel” should mean an agent’s behavior is **observable, measurable, comparable, and improvable**.

---

## 4. Product Principles

| Principle | Meaning |
|---|---|
| **Observe, don’t own** | Never become the agent runtime; integrate via SDKs, exporters, and plugins |
| **Trace is the source of truth** | Every insight derives from a canonical execution trace model |
| **Framework-agnostic core** | First-class support via adapters; core never depends on a single framework |
| **Evaluation is explicit** | Scores require declared rubrics, checks, or judges—no magic “quality” |
| **Reproducibility over vibes** | Benchmarks pin versions, seeds, datasets, and configs |
| **Open by default** | Schema, APIs, and adapters are public; vendor lock-in is a failure mode |
| **Progressive depth** | Start with traces and metrics; grow into evals, leaderboards, and CI gates |

---

## 5. Target Users

| Persona | Needs |
|---|---|
| **Agent engineer** | Debug a failed run; see which tool/step failed and why |
| **ML / applied AI engineer** | Compare models, prompts, planners, memory strategies |
| **Platform / infra engineer** | Cost, latency, reliability SLOs for agent services |
| **QA / eval engineer** | Suites, rubrics, regression detection, CI integration |
| **Researcher** | Reproducible benchmarks across frameworks and configs |
| **Open-source maintainer** | Plugin surface for new frameworks without forking core |

---

## 6. Core Jobs To Be Done

1. **Instrument** an agent once and get structured traces everywhere.
2. **Inspect** a single run end-to-end (timeline, costs, errors, retries).
3. **Evaluate** runs against task success and quality rubrics.
4. **Benchmark** configurations (model × planner × tools × memory).
5. **Detect regressions** when a new agent version ships.
6. **Attribute** time and money to tools, models, and steps.
7. **Share** results via dashboards, exports, and CI reports.

---

## 7. Product Surfaces (Long-Term)

```text
┌─────────────────────────────────────────────────────────────┐
│                     Sentinel AI Platform                      │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  SDKs /      │  Ingestion   │  Analysis    │  Experience    │
│  Adapters    │  & Store     │  Engine      │  Layer         │
│              │              │              │                │
│  Python/TS   │  API / OTLP  │  Metrics     │  UI / CLI      │
│  Framework   │  Event bus   │  Evals       │  Reports / CI  │
│  plugins     │  Trace DB    │  Benchmarks  │  Public API    │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

---

## 8. Success Metrics (North Stars)

| Metric | Intent |
|---|---|
| Time-to-first-trace | Minutes from install to useful timeline |
| Framework coverage | Number of stable official adapters |
| Eval adoption | % of projects with at least one scored suite |
| Regression catch rate | Regressions detected before production (self-reported + CI) |
| Cost attribution coverage | % of spend mapped to model/tool/step |
| Community plugins | Third-party adapters without core changes |

---

## 9. Positioning

| Sentinel AI **is** | Sentinel AI **is not** |
|---|---|
| Agent APM + eval + benchmark platform | An agent framework |
| Open schema + SDKs + UI | A closed SaaS-only black box |
| Complementary to LangSmith / Phoenix / Braintrust | A drop-in clone of any one of them |
| Framework-neutral | Locked to OpenAI, LangChain, or one vendor |

---

## 10. Out of Scope for Early Phases

- Multi-tenant commercial SaaS billing (may come later as a hosted offering)
- Training or fine-tuning models
- Automatic agent rewriting / auto-healing without human-defined policies
- Guaranteeing correctness of third-party agents

---

## Related Documents

- [Functional Requirements](./01-functional-requirements.md)
- [High-Level Architecture](./03-high-level-architecture.md)
- [ROADMAP](../../ROADMAP.md)
