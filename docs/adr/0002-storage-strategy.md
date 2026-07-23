# ADR-0002: Storage Strategy (Postgres + Object Store)

- **Status:** Accepted
- **Date:** 2026-07-23

## Context

Traces mix highly selective metadata queries (list runs by tag/version) with large, infrequently scanned payloads (full prompts). A single storage technology optimizes poorly for both.

## Decision

Use a **dual-store** approach:

1. **PostgreSQL** for projects, run indices, span metadata, events summary, scores, suites, and API keys.
2. **Object store** (local filesystem in dev; S3-compatible in deployment) for large payloads, attachments, and bulk exports.
3. Defer dedicated OLAP (ClickHouse/DuckDB) until Postgres aggregations become a proven bottleneck.

## Consequences

### Positive

- Fast transactional UX for run lists and eval gates
- Cheap retention for bulky text
- Familiar ops for self-hosters

### Negative

- Application-level joins between metadata and payloads
- Backup must cover both systems

### Follow-ups

- Retention policies and hot/cold tiering in a later phase
- Parquet export for data-science workflows
