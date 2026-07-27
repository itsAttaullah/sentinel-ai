"""Minimal custom-adapter example (file export)."""

from __future__ import annotations

import sys
from pathlib import Path

from sentinel_ai import FileExporter, Tracer
from sentinel_adapter_custom import CustomAdapter


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else Path(__file__).parent / "out" / "traces.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)

    tracer = Tracer(
        project_id="proj_demo",
        exporter=FileExporter(out),
        agent_name="custom-ref-agent",
        agent_version="0.1.0",
        flush_interval_seconds=None,
    )
    adapter = CustomAdapter()
    adapter.bind(tracer)

    with adapter.start_run(name="adapter-smoke", attributes={"task": "demo"}):
        with adapter.planner_span(planner_name="react", plan=["think", "act"]):
            pass
        with adapter.llm_span(provider="openai", model="gpt-4.1-mini", tokens_in=12, tokens_out=8):
            pass
        with adapter.tool_span("web_search", input={"query": "sentinel adapters"}):
            adapter.record_event(type="log", message="tool finished", level="info")

    tracer.shutdown()
    print(f"Wrote {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
