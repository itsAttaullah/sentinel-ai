# Phase 5 — CLI & Developer Experience

| Field | Value |
|---|---|
| **Status** | Complete |
| **Branch** | `feat/cli-dx` |
| **Depends on** | Phase 3 (+ Phase 4 recommended) |

## Objectives

- Ship `sentinel` CLI for init, config, upload, query  
- Improve onboarding docs and samples  
- CI-friendly non-interactive commands  

## In Scope (delivered)

- `apps/cli` package with `sentinel` entrypoint (Typer)
- Commands: `init`, `config show`, `whoami`, `health`, `upload`, `projects list`, `runs list|get`, `metrics`, `serve`, `version`
- Config resolution: flags → env → `.sentinel/config.toml` → defaults
- `--json` output + non-zero exit codes for CI
- Unit tests + README/docs updates

## Out of Scope

- Full web UX  
- Adapter generation  
- Starting Docker as a subprocess daemon  

## Exit Criteria

- [x] CLI documented in README quickstart  
- [x] Upload + query path works against local Compose  

## Suggested Commit Message

```text
feat: add Sentinel CLI for local ingest and query workflows
```

## Suggested PR Title

`feat: Sentinel CLI for local ingest and query workflows`

## Manual Testing Checklist

- [ ] `pip install -e ".\apps\cli[dev]"`
- [ ] `pytest .\apps\cli\tests -q`
- [ ] `docker compose up --build` (or existing stack)
- [ ] `sentinel init`
- [ ] `sentinel upload .\packages\schema\fixtures\valid\ingest-batch.hello.json`
- [ ] `sentinel runs get run_hello_001 --json`
- [ ] `sentinel metrics --json`
