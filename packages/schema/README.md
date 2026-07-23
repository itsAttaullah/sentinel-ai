# @sentinel-ai/schema

Canonical **Agent Trace Schema** and HTTP API contracts for Sentinel AI.

This package is the source of truth for:

- JSON Schema definitions (`Run`, `Span`, `Event`, `IngestBatch`)
- Golden fixtures (valid + invalid)
- OpenAPI stub for ingest and control-plane routes
- Versioning / compatibility policy

No runtime server or SDK logic lives here.

---

## Current version

| Contract | Version |
|---|---|
| Trace wire schema (`schema_version`) | `1.0.0` |
| OpenAPI (`info.version`) | `0.1.0` (stub; not implemented) |

---

## Layout

```text
packages/schema/
├── README.md
├── VERSIONING.md
├── jsonschema/
│   └── v1/
│       ├── common.schema.json
│       ├── run.schema.json
│       ├── span.schema.json
│       ├── event.schema.json
│       └── ingest-batch.schema.json
├── fixtures/
│   ├── valid/
│   └── invalid/
└── openapi/
    └── openapi.yaml
```

---

## Core entities

| Entity | Purpose |
|---|---|
| **Run** | One agent execution (root timeline) |
| **Span** | Timed unit of work (`llm`, `tool`, `planner`, `memory`, `agent`, `custom`) |
| **Event** | Point-in-time signal (`retry`, `error`, `log`, `checkpoint`, `feedback`, `custom`) |
| **IngestBatch** | Envelope posted to ingest containing runs/spans/events |

See [VERSIONING.md](./VERSIONING.md) and [docs/architecture](../../docs/architecture/README.md).

---

## Validation (for implementers)

Validators belong in later phases (SDK / server). For manual checks, any JSON Schema 2020-12 validator may be used against files in `jsonschema/v1/` and `fixtures/`.

---

## Related

- [ADR-0001 Canonical Trace Schema](../../docs/adr/0001-canonical-trace-schema.md)
- [Phase 1 notes](../../docs/phases/phase-01-schema-contracts.md)
- [Trace Schema Reference v1](../../docs/architecture/09-trace-schema-v1.md)
