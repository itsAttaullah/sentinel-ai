"""Unit tests for LangGraph normalized event adapter."""

from __future__ import annotations

from sentinel_ai import FileExporter, Tracer
from sentinel_adapter_langgraph import LangGraphAdapter


def test_langgraph_normalized_events(tmp_path) -> None:
    path = tmp_path / "lg.jsonl"
    tracer = Tracer(
        project_id="proj_demo",
        exporter=FileExporter(path),
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
            "name": "chat",
            "model": "gpt-x",
            "provider": "openai",
        }
    )
    adapter.handle_event(
        {"type": "llm_end", "run_id": "l1", "tokens_in": 4, "tokens_out": 6}
    )
    adapter.handle_event(
        {
            "type": "tool_start",
            "run_id": "t1",
            "parent_run_id": "c1",
            "tool_name": "lookup",
        }
    )
    adapter.handle_event(
        {"type": "tool_end", "run_id": "t1", "output": {"ok": True}}
    )
    adapter.handle_event({"type": "chain_end", "run_id": "c1"})
    adapter.end_run()
    tracer.shutdown()

    body = path.read_text(encoding="utf-8")
    assert "gpt-x" in body
    assert "lookup" in body
    assert "adapter:langgraph" in body or "langgraph" in body
