# Backup and restore

Self-hosted Sentinel stores primary state in **Postgres**. Object/file exporters (SDK JSONL) are optional sidecars and are not a substitute for DB backups.

## What to back up

| Asset | Notes |
|---|---|
| Postgres database | Projects, runs, spans, events, metrics, evals, benchmarks, regression jobs |
| `SENTINEL_*` env / Compose secrets | Auth keys, DB URL, redaction mode |
| Optional pricing override file | If `SENTINEL_PRICING_PATH` points outside the repo |
| Uploaded JSONL archives | Only if you rely on file exporters for offline replay |

## Postgres dump (Compose)

```powershell
docker compose exec postgres pg_dump -U sentinel -d sentinel -Fc -f /tmp/sentinel.dump
docker compose cp postgres:/tmp/sentinel.dump .\backups\sentinel.dump
```

## Restore

```powershell
docker compose cp .\backups\sentinel.dump postgres:/tmp/sentinel.dump
docker compose exec postgres pg_restore -U sentinel -d sentinel --clean --if-exists /tmp/sentinel.dump
```

Stop the API during restore if you need a consistent cutover:

```powershell
docker compose stop api
# restore
docker compose start api
```

## Verification

```powershell
sentinel health
curl http://localhost:8080/readyz
```

Confirm a known `project_id` / `run_id` still resolves via the API or web UI.

## Retention tips

- Schedule dumps (daily) and keep at least one off-host copy
- Test restore on a scratch database before you need it
- Quarantine rows are also in Postgres — include them if you debug ingest failures
