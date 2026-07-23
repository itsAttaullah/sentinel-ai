# ADR-0004: SDK-First Instrumentation

- **Status:** Accepted
- **Date:** 2026-07-23

## Context

Supporting many frameworks immediately risks shallow, broken adapters and a muddy core model. The highest leverage artifact is a clean SDK that expresses agent semantics correctly.

## Decision

1. Build and dogfood a **first-party SDK** (Python first) against custom/hello-world agents.
2. Stabilize the canonical schema and export path.
3. Add framework adapters **after** SDK + server ingest work.
4. Treat adapters as plugins with conformance tests—not as core dependencies.

## Consequences

### Positive

- Better schema quality
- Adapters become thin maps
- Custom runtimes are first-class from day one

### Negative

- Delayed “one-click LangGraph” experience
- Early users must instrument manually or wait for adapters

### Mitigation

Ship excellent docs and a hello-trace example in the phase that introduces the SDK.
