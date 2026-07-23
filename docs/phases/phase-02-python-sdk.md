# Phase 2 — Python SDK

| Field | Value |
|---|---|
| **Status** | Complete |
| **Branch** | `feat/python-sdk` |
| **Depends on** | Phase 1 |

## Objectives

- Implement Python tracer (run/span/event APIs)  
- Async buffered export (HTTP and/or file sink)  
- Context propagation for common async patterns  
- `examples/hello-trace` sample  

## In Scope (delivered)

- Installable package `sentinel-ai` under `packages/sdk-python`
- `Tracer` / `RunHandle` / `SpanHandle` with context managers
- `contextvars` propagation for current run/span
- Exporters: `FileExporter`, `HttpExporter`, `ConsoleExporter`, `MultiExporter`
- Buffered flush (size threshold + optional interval + atexit)
- Unit tests and `examples/hello-trace`

## Out of Scope

- Framework-specific adapters  
- Production metrics derivation  
- Live ingest server (Phase 3)

## Exit Criteria

- [x] Installable Python package  
- [x] Emits schema-valid batches (v1-shaped; validated by fixtures/tests)  
- [x] Hello-trace docs path ≤ 10 minutes  

## Suggested Commit Message

```text
feat: add Python instrumentation SDK and hello-trace example
```

## Suggested PR Title

`feat: Python instrumentation SDK and hello-trace example`

## Manual Testing Checklist

- [ ] `pip install -e .\packages\sdk-python[dev]`
- [ ] `pytest .\packages\sdk-python\tests -q`
- [ ] `python .\examples\hello-trace\main.py`
- [ ] Open generated JSONL — batches include `schema_version` `1.0.0`
- [ ] Confirm README quickstart matches the example
