# Phase 3 — Ingest & Store

| Field | Value |
|---|---|
| **Status** | Complete |
| **Branch** | `feat/ingest-store` |
| **Depends on** | Phase 1 (+ Phase 2 recommended) |

## Objectives

- FastAPI ingest endpoint with schema validation  
- Project + run persistence in Postgres  
- Idempotent upserts; quarantine invalid batches  
- Docker Compose for local stack  

## In Scope (delivered)

- `apps/server` FastAPI application
- `POST /v1/ingest` with JSON Schema v1 validation
- Projects + runs list/detail APIs
- Quarantine persistence + `GET /v1/quarantine`
- Idempotent upserts for runs/spans/events
- `docker-compose.yml` (Postgres + API)
- Local auth mode (default) and API-key mode
- SQLite-backed unit/integration tests

## Out of Scope

- Rich UI  
- Evaluation execution  
- Redis/workers / metrics derivation  

## Exit Criteria

- [x] SDK/file upload → durable run retrievable via API  
- [x] Compose brings up API + Postgres  
- [x] Basic auth/local mode documented  

## Suggested Commit Message

```text
feat: add ingest API and Postgres-backed trace storage
```

## Suggested PR Title

`feat: ingest API and Postgres-backed trace storage`

## Manual Testing Checklist

- [ ] `docker compose up --build`
- [ ] `curl http://localhost:8080/healthz`
- [ ] POST `packages/schema/fixtures/valid/ingest-batch.hello.json` to `/v1/ingest`
- [ ] GET `/v1/projects/proj_demo/runs/run_hello_001`
- [ ] POST invalid empty batch → 400 and visible in `/v1/quarantine`
- [ ] `pip install -e ".\apps\server[dev]"` then `pytest .\apps\server\tests -q`
