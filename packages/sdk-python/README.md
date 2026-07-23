# Sentinel AI — Python SDK

Instrument autonomous agents and emit **canonical Sentinel traces** (`schema_version` `1.0.0`).

This SDK does **not** run agents. It records runs, spans, and events and exports them to a file and/or HTTP ingest endpoint.

---

## Install (local editable)

From the repository root:

```powershell
pip install -e .\packages\sdk-python
```

With tests:

```powershell
pip install -e ".\packages\sdk-python[dev]"
pytest .\packages\sdk-python\tests -q
```

---

## Quick start (file export)

```python
from sentinel_ai import FileExporter, Tracer

tracer = Tracer(
    project_id="proj_demo",
    exporter=FileExporter("traces.jsonl"),
    agent_name="demo-agent",
    agent_version="0.1.0",
)

with tracer.start_run(name="answer-user-question") as run:
    with tracer.start_span(
        kind="llm",
        name="chat.completions",
        llm={
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "tokens_in": 120,
            "tokens_out": 45,
        },
    ):
        pass

    with tracer.start_span(
        kind="tool",
        name="web_search",
        tool={"tool_name": "web_search", "input": {"query": "Sentinel AI"}},
    ):
        pass

tracer.flush()
tracer.shutdown()
print(run.run_id)
```

See [`examples/hello-trace`](../../examples/hello-trace) for a full walkthrough.

---

## Exporters

| Exporter | Purpose |
|---|---|
| `FileExporter` | Append `IngestBatch` JSON lines (offline / CI) |
| `HttpExporter` | `POST /v1/ingest` (server comes in a later phase) |
| `ConsoleExporter` | Print batches (debug) |
| `MultiExporter` | Fan-out to several exporters |

---

## Context propagation

Current run/span are stored in `contextvars`, so they propagate across `asyncio` tasks created while a run/span is active.

---

## Schema

Emitted payloads follow [`packages/schema`](../schema/README.md) v1.
