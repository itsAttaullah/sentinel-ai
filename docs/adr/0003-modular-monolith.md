# ADR-0003: Modular Monolith + Workers

- **Status:** Accepted
- **Date:** 2026-07-23

## Context

Early microservice splits (ingest-service, eval-service, UI-BFF, …) increase operational burden before product-market fit. A single deployable with clear modules ships faster for an OSS self-hosted MVP.

## Decision

Implement the server as a **modular monolith**:

- One primary API process (ingest + control plane routes)
- Async **workers** in the same codebase for metrics derivation, eval jobs, and maintenance
- Redis (or equivalent) as the job/queue backbone for MVP
- Strict package boundaries enforced by convention and CI linting later

Split into separately scalable services only when metrics justify it (ingest CPU vs query CPU, etc.).

## Consequences

### Positive

- Simple Docker Compose
- Shared types and transactions where needed
- Faster contributor onboarding

### Negative

- Requires discipline to avoid tight coupling
- Noisy-neighbor risk inside one process under load

### Escape hatch

Extract ingest or workers to separate services without changing the external schema/API.
