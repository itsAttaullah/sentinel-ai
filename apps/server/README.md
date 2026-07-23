# Sentinel AI Server

Self-hosted **ingest gateway + control plane** for Sentinel AI.

Phase 3 scope:

- `POST /v1/ingest` with JSON Schema v1 validation
- Postgres persistence for projects, runs, spans, events
- Idempotent upserts
- Quarantine store for invalid batches
- Docker Compose (API + Postgres)
- Local auth mode (no API key) by default

---

## Quick start (Compose)

From the repository root:

```powershell
docker compose up --build
```

API: http://localhost:8080  
Health: http://localhost:8080/healthz

### Ingest a fixture

```powershell
curl -s -X POST http://localhost:8080/v1/ingest `
  -H "Content-Type: application/json" `
  --data-binary "@packages/schema/fixtures/valid/ingest-batch.hello.json"
```

### Fetch the run

```powershell
curl -s http://localhost:8080/v1/projects/proj_demo/runs/run_hello_001
```

---

## Local dev (without Docker for the API)

1. Start Postgres (Compose db only is fine):

```powershell
docker compose up postgres -d
```

2. Install and run:

```powershell
pip install -e ".\apps\server[dev]"
$env:SENTINEL_DATABASE_URL = "postgresql+psycopg://sentinel:sentinel@localhost:5432/sentinel"
$env:SENTINEL_SCHEMA_DIR = "$PWD\packages\schema\jsonschema\v1"
$env:SENTINEL_AUTH_MODE = "local"
uvicorn sentinel_server.main:app --reload --port 8080
```

---

## Auth modes

| Mode | Env | Behavior |
|---|---|---|
| `local` (default) | `SENTINEL_AUTH_MODE=local` | No API key required |
| `api_key` | `SENTINEL_AUTH_MODE=api_key` + `SENTINEL_API_KEYS=key1,key2` | Require `X-Sentinel-Api-Key` |

---

## Environment

| Variable | Default | Meaning |
|---|---|---|
| `SENTINEL_DATABASE_URL` | `postgresql+psycopg://sentinel:sentinel@localhost:5432/sentinel` | SQLAlchemy URL |
| `SENTINEL_SCHEMA_DIR` | auto-detect monorepo `packages/schema/jsonschema/v1` | JSON Schema path |
| `SENTINEL_AUTH_MODE` | `local` | `local` \| `api_key` |
| `SENTINEL_API_KEYS` | empty | Comma-separated keys |
| `SENTINEL_MAX_BODY_BYTES` | `10485760` (10 MiB) | Ingest body limit |

---

## Out of scope (later phases)

- Metrics derivation workers
- Evaluation / benchmarks
- Redis queue
- Web UI
