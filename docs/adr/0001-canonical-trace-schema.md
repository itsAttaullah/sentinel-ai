# ADR-0001: Canonical Agent Trace Schema

- **Status:** Accepted
- **Date:** 2026-07-23
- **Deciders:** Principal architecture (Phase 0)

## Context

Agent frameworks expose incompatible lifecycle hooks and log formats. Without a shared model, Sentinel cannot compare runs across LangGraph, CrewAI, custom runtimes, and others. Pure OpenTelemetry HTTP/DB spans miss agent-native concepts (planner steps, memory ops, retries, tool loops).

## Decision

Sentinel defines a **Canonical Agent Trace Schema** as the system of record for all ingested telemetry.

1. Wire format: versioned JSON (JSON Schema draft 2020-12).
2. Core entities: `Run`, `Span`, `Event`, plus `IngestBatch` envelope.
3. Typed span `kind` values: `llm`, `tool`, `planner`, `memory`, `agent`, `custom`.
4. Required correlation fields: `schema_version`, `project_id`, `run_id`, `span_id` / `event_id`, timestamps, status.
5. Optional rich payloads: prompts, completions, tool I/O—subject to redaction policies.
6. Framework adapters **must** map into this schema; they must not invent parallel persistence models.
7. Alignment with OpenTelemetry GenAI conventions is encouraged via a mapping layer, but OTel is not the only ingest path.

### Concrete v1 location (Phase 1)

- Schemas: `packages/schema/jsonschema/v1/`
- Fixtures: `packages/schema/fixtures/`
- Version policy: `packages/schema/VERSIONING.md`
- Human reference: `docs/architecture/09-trace-schema-v1.md`
- Initial wire version: `schema_version = "1.0.0"`

## Consequences

### Positive

- Cross-framework benchmarks become possible
- UI and evaluators depend on one model
- Clear conformance tests for adapters

### Negative

- Ongoing schema governance burden
- Mapping effort for each framework
- Potential overlap/conflict with emerging OTel conventions (manage via explicit mapping ADR later)

### Neutral

- Protobuf/OTLP may be added later as alternate encodings of the same logical model
