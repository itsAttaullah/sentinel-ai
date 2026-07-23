# Phase 1 — Schema & Contracts

| Field | Value |
|---|---|
| **Status** | Complete |
| **Branch** | `feat/schema-contracts` |
| **Depends on** | Phase 0 |

## Objectives

- Publish versioned JSON Schema for Run, Span, Event  
- Define compatibility and versioning policy  
- Provide golden fixtures for valid/invalid payloads  
- Stub OpenAPI for ingest and core control-plane routes  

## In Scope (delivered)

- `packages/schema` package with JSON Schema v1.0.0
- `VERSIONING.md` compatibility policy
- Valid + invalid golden fixtures
- OpenAPI 3.1 stub (`packages/schema/openapi/openapi.yaml`)
- Architecture reference `docs/architecture/09-trace-schema-v1.md`
- ADR-0001 updated with concrete v1 paths

## Out of Scope

- Live server persistence  
- Full SDK implementation  
- UI  
- Automated schema CI validator (deferred to SDK/server phases)

## Exit Criteria

- [x] Schema package layout exists with documented versions  
- [x] Fixtures + validation examples documented  
- [x] OpenAPI stub checked in  
- [x] ADR updates if schema decisions change  

## Suggested Commit Message

```text
feat: introduce canonical agent trace schema and API stubs

Add JSON Schema v1 for runs/spans/events/batches, golden fixtures,
versioning policy, and OpenAPI contract stubs.
```

## Suggested PR Title

`feat: canonical agent trace schema and API stubs`

## Manual Testing Checklist

- [ ] Open `packages/schema/README.md` — links resolve
- [ ] Skim `VERSIONING.md` — semver rules clear
- [ ] Spot-check a valid fixture against the matching schema fields
- [ ] Confirm each invalid fixture README reason matches the payload
- [ ] Open `openapi/openapi.yaml` in an editor / Swagger preview
- [ ] Confirm `docs/architecture/09-trace-schema-v1.md` renders Mermaid
