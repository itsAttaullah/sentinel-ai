# ADR-0005: License & Open-Source Posture

- **Status:** Proposed
- **Date:** 2026-07-23

## Context

Sentinel AI is intended as an open-source platform. License choice affects adoption by companies, ability to offer a hosted commercial edition, and contributor expectations.

## Decision (Proposed)

Defer final license file until maintainers confirm go-to-market posture. Recommended default:

- **Apache-2.0** for core, schema, SDKs, and official adapters

Rationale: patent grant + broad corporate acceptance; compatible with most agent ecosystem libraries.

Alternative: **MIT** if maximum permissiveness is preferred and patent grant is not required.

## Consequences

### Positive

- Clear signal to contributors once chosen
- Apache-2.0 eases enterprise legal review

### Negative

- Delay may confuse early visitors (mitigate via README note)

### Non-decision

Trademark, CLA/DCO, and governance model to be decided before public launch.
