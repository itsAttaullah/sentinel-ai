# ADR-0007: Framework Adapters as Plugins

- **Status:** Accepted
- **Date:** 2026-07-23

## Context

Agent frameworks evolve quickly and pull heavy dependencies. Embedding them in the Sentinel server or core SDK would create dependency hell and version conflicts.

## Decision

1. Official adapters ship as **separate packages** under `packages/adapters/*`.
2. Server and core SDK never depend on framework packages.
3. A **conformance suite** defines “official adapter” quality bar.
4. Community adapters are first-class via documented plugin interfaces.
5. Adapter versioning tracks both Sentinel schema version and framework version ranges.

## Consequences

### Positive

- Core stays lean
- Framework churn isolated
- Community can extend without forking

### Negative

- More packages to release
- Discovery/docs burden

### Target adapter list (non-binding order)

Custom → ForgeMind / Research Agent → OpenAI Agents SDK → LangGraph → CrewAI → PydanticAI → others

### Concrete locations (Phase 9)

- Plugin protocol: `packages/adapters/base` (`sentinel-adapter-base`)
- Reference custom adapter: `packages/adapters/custom`
- LangGraph adapter: `packages/adapters/langgraph` (optional `langchain-core`)
- Conformance suite: `packages/adapters/conformance`
- Discovery entry-point group: `sentinel.adapters`
