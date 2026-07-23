# Phase 3 — Ingest & Store

| Field | Value |
|---|---|
| **Status** | Not started |
| **Branch (suggested)** | `feat/phase-3-ingest-store` |
| **Depends on** | Phase 1 (Phase 2 recommended) |

## Objectives

- FastAPI ingest endpoint with schema validation  
- Project + run persistence in Postgres  
- Idempotent upserts; quarantine invalid batches  
- Docker Compose for local stack  

## Out of Scope

- Rich UI  
- Evaluation execution  

## Exit Criteria

- [ ] SDK/file upload → durable run retrievable via API  
- [ ] Compose brings up API + Postgres (+ Redis if needed)  
- [ ] Basic auth/local mode documented  

## Suggested Commit Message

```text
feat: add ingest API and Postgres-backed trace storage
```

## Suggested PR Title

`feat: Phase 3 — Ingest and storage`
