# Phase 1 — Schema & Contracts

| Field | Value |
|---|---|
| **Status** | Not started |
| **Branch (suggested)** | `feat/phase-1-schema-contracts` |
| **Depends on** | Phase 0 |

## Objectives

- Publish versioned JSON Schema for Run, Span, Event  
- Define compatibility and versioning policy  
- Provide golden fixtures for valid/invalid payloads  
- Stub OpenAPI for ingest and core control-plane routes  

## Out of Scope

- Live server persistence  
- Full SDK implementation  
- UI  

## Exit Criteria

- [ ] Schema package layout exists with documented versions  
- [ ] Fixtures + validation examples documented  
- [ ] OpenAPI stub checked in  
- [ ] ADR updates if schema decisions change  

## Suggested Commit Message

```text
feat: introduce canonical agent trace schema and API stubs
```

## Suggested PR Title

`feat: Phase 1 — Canonical schema and contracts`
