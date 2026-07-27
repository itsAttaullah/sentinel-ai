# Architecture Decision Records

This directory holds ADRs for Sentinel AI.

## Format

Each ADR uses:

- Title
- Status (`Proposed` | `Accepted` | `Superseded` | `Deprecated`)
- Context
- Decision
- Consequences

## Index

| ADR | Title | Status |
|---|---|---|
| [0001](./0001-canonical-trace-schema.md) | Canonical Agent Trace Schema | Accepted |
| [0002](./0002-storage-strategy.md) | Storage Strategy (Postgres + Object Store) | Accepted |
| [0003](./0003-modular-monolith.md) | Modular Monolith + Workers | Accepted |
| [0004](./0004-sdk-first-instrumentation.md) | SDK-First Instrumentation | Accepted |
| [0005](./0005-license-and-open-source-posture.md) | License & Open-Source Posture | Accepted |
| [0006](./0006-evaluation-model.md) | Explicit Versioned Evaluation Model | Accepted |
| [0007](./0007-framework-adapters-as-plugins.md) | Framework Adapters as Plugins | Accepted |

## When to Write an ADR

Write an ADR when a decision:

- Changes package boundaries or deployment topology
- Introduces a new persistent data model
- Chooses a technology that is hard to reverse
- Affects external compatibility (schema, API, adapters)
