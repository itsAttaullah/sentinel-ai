# Hello Trace — Sentinel AI Python SDK

Emit a schema v1 ingest batch to a local JSONL file in under 10 minutes.

## 1. Install the SDK (editable)

From the repository root:

```powershell
pip install -e .\packages\sdk-python
```

## 2. Run the sample

```powershell
python .\examples\hello-trace\main.py
```

Optional custom output path:

```powershell
python .\examples\hello-trace\main.py .\examples\hello-trace\out\my-traces.jsonl
```

## 3. Inspect output

Open the JSONL file (default: `examples/hello-trace/out/traces.jsonl`).  
Each line is an `IngestBatch` matching `packages/schema` v1.

## What it demonstrates

- `Tracer.start_run` / nested spans (`agent`, `llm`, `tool`, `planner`, `memory`)
- `record_event` for a retry signal
- `FileExporter` for offline / CI-friendly capture
- `flush` / `shutdown`

HTTP ingest (`HttpExporter`) is available in the SDK but needs the Phase 3 server.
