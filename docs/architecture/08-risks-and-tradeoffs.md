# Risks and Trade-offs

**Document:** Architecture Proposal — Risks & Trade-offs  
**Status:** Active living document

---

## 1. Key Trade-offs

| Decision | Benefit | Cost |
|---|---|---|
| **Sidecar platform (not a runtime)** | Clear positioning; framework-agnostic | Cannot “just run” agents; needs integration |
| **Canonical proprietary-friendly schema** (inspired by OTel, agent-native) | Fits planners/tools/memory better than pure HTTP spans | Must maintain mapping to OTel; dual-mindset risk |
| **Modular monolith + workers** | Fast delivery, simple ops | Must enforce package boundaries or it becomes a ball of mud |
| **Postgres first** | Strong consistency for scores/projects | Heavy analytical queries may need later OLAP |
| **SDK-first, adapters second** | Correctness of core model before framework chase | Slower “works with LangGraph out of the box” story |
| **Self-host first** | Trust, OSS credibility, data residency | Hosted UX/billing deferred; growth loop slower |
| **LLM-as-judge as optional** | Captures subjective quality | Cost, flakiness, need versioning & caching |
| **At-least-once ingest** | Durability under failure | Requires idempotency everywhere |
| **Redaction at multiple layers** | Defense in depth | Complexity; risk of over-redacting debug value |

---

## 2. Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R01 | Schema churn breaks early adopters | Med | High | Semver + compatibility windows + golden fixtures |
| R02 | Adapter maintenance burden across frameworks | High | High | Conformance suite; adapters as separate packages; community plugins |
| R03 | Overlap perception vs LangSmith/Phoenix/Braintrust | High | Med | Clear differentiation: open schema, self-host, multi-framework benchmarks |
| R04 | PII leakage via prompt/tool payloads | Med | High | Default redaction policies; docs; ingest filters |
| R05 | Eval flakiness undermines CI trust | Med | High | Deterministic gates by default; judges quarantined/statistically aggregated |
| R06 | Scope creep into “building agents” | Med | High | Explicit non-goals; PR review checklist |
| R07 | Performance overhead scares production users | Med | Med | Async export, sampling, benchmarks published |
| R08 | Single-language server limits TS contributors | Low | Med | OpenAPI + TS client; consider Go/TS server only if needed later |
| R09 | Cost estimation inaccuracy | High | Low | Versioned price tables; allow user overrides; show “estimate” clearly |
| R10 | Empty-roadmap fatigue (docs without code) | Med | Med | Short Phase 0; Phase 1 delivers schema + hello-trace quickly |

---

## 3. Competitive / Ecosystem Risks

- **Framework vendors** may ship competing observability.  
  → Compete on openness, portability, and benchmark rigor—not lock-in.
- **OTel GenAI semantic conventions** may standardize overlapping fields.  
  → Align where possible; extend for agent-specific concepts (planner, memory, retries).
- **Eval startups** move fast on UX.  
  → Prioritize excellent run timeline + regression diffs; don’t boil the ocean.

---

## 4. Technical Debt We Accept Early

1. JSON-only ingest (no protobuf)  
2. Redis queue instead of a heavier log bus  
3. Single region / single node happy path  
4. Manual pricing tables  
5. Limited RBAC (API keys before full IAM)

Each item has a deliberate later phase or ADR escape hatch.

---

## 5. What Would Make Us Revisit Architecture

- Ingest > tens of thousands of events/sec sustained on customer deployments  
- Strong demand for pure OTLP-only pipelines  
- Need for multi-tenant hosted SaaS with hard isolation  
- Breakthrough standard for agent traces that obsoletes our schema  

Revisit via new ADRs—do not silently rewrite.

---

## Related Documents

- [Non-Functional Requirements](./02-non-functional-requirements.md)
- [Technology Recommendations](./06-technology-recommendations.md)
- [ADR index](../adr/README.md)
