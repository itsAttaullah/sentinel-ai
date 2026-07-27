# ADR-0005: License & Open-Source Posture

- **Status:** Accepted
- **Date:** 2026-07-27
- **Deciders:** Maintainers (Phase 11 hardening)

## Context

Sentinel AI is intended as an open-source platform. License choice affects adoption by companies, ability to offer a hosted commercial edition, and contributor expectations.

## Decision

Use **Apache-2.0** for core, schema, SDKs, CLI, server, and official adapters.

Rationale: patent grant + broad corporate acceptance; compatible with most agent ecosystem libraries.

The canonical license text is the repository root [`LICENSE`](../../LICENSE) file.

## Consequences

### Positive

- Clear signal to contributors and enterprises
- Apache-2.0 eases legal review

### Negative

- Slightly more attribution ceremony than MIT

### Follow-ups

- Trademark / CLA / governance remain optional and can be added later without relicensing
