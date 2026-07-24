# Sentinel AI CLI

Developer CLI for local and CI workflows against the Sentinel API.

## Install

With the repo venv active:

```powershell
pip install -e ".\apps\cli[dev]"
sentinel --help
```

## Commands

| Command | Purpose |
|---|---|
| `sentinel init` | Write `.sentinel/config.toml` |
| `sentinel config show` | Print resolved config |
| `sentinel whoami` | Config + API health check |
| `sentinel health` | Hit `/healthz` |
| `sentinel upload PATH` | Upload JSON/JSONL ingest batches |
| `sentinel projects list` | List projects |
| `sentinel runs list` | List runs for the configured project |
| `sentinel runs get RUN_ID` | Fetch run detail (spans/events/metrics) |
| `sentinel metrics` | Project metrics aggregates |
| `sentinel serve` | Print how to start the local stack |

All commands support `--json` for machine-readable output (CI-friendly).

## Config resolution (highest wins)

1. CLI flags (`--api-url`, `--project-id`, `--api-key`)
2. Environment: `SENTINEL_API_URL`, `SENTINEL_PROJECT_ID`, `SENTINEL_API_KEY`
3. `./.sentinel/config.toml`
4. Defaults (`http://localhost:8080`, project `proj_demo`)

## Quick example

```powershell
sentinel init --project-id proj_demo
sentinel health
sentinel upload .\packages\schema\fixtures\valid\ingest-batch.hello.json
sentinel runs get run_hello_001
sentinel metrics
```
