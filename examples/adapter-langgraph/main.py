"""LangGraph normalized-event smoke example (no LangGraph install required)."""

from __future__ import annotations

import sys
from pathlib import Path

from sentinel_ai import FileExporter, Tracer
from sentinel_adapter_langgraph import LangGraphAdapter


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else Path(__file__).parent / "out" / "traces.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)

    tracer = Tracer(
        project_id="proj_demo",
        exporter=FileExporter(out),
        flush_interval_seconds=None,
    )
    adapter = LangGraphAdapter()
    adapter.bind(tracer)

    adapter.handle_event({"type": "chain_start", "name": "agent", "run_id": "c1"})
    adapter.handle_event(
        {
            "type": "llm_start",
            "run_id": "l1",
            "parent_run_id": "c1",
            "model": "gpt-4.1-mini",
            "provider": "openai",
        }
    )
    adapter.handle_event(
        {"type": "llm_end", "run_id": "l1", "tokens_in": 20, "tokens_out": 12}
    )
    adapter.handle_event(
        {
            "type": "tool_start",
            "run_id": "t1",
            "parent_run_id": "c1",
            "tool_name": "web_search",
            "input": {"query": "sentinel"},
        }
    )
    adapter.handle_event(
        {"type": "tool_end", "run_id": "t1", "output": {"hits": 1}}
    )
    adapter.handle_event({"type": "chain_end", "run_id": "c1"})
    adapter.end_run()
    tracer.shutdown()
    print(f"Wrote {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
