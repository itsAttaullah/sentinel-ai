"""Unit tests for custom reference adapter."""

from __future__ import annotations

from sentinel_ai import FileExporter, Tracer
from sentinel_adapter_custom import CustomAdapter


def test_custom_adapter_emits_spans(tmp_path) -> None:
    path = tmp_path / "out.jsonl"
    tracer = Tracer(
        project_id="proj_demo",
        exporter=FileExporter(path),
        flush_interval_seconds=None,
    )
    adapter = CustomAdapter()
    adapter.bind(tracer)

    with adapter.start_run(name="demo"):
        with adapter.llm_span(provider="openai", model="gpt-test"):
            pass
        with adapter.tool_span("echo", input={"x": 1}, output={"y": 2}):
            adapter.record_event(type="log", message="ok", level="info")

    tracer.shutdown()
    text = path.read_text(encoding="utf-8")
    assert "gpt-test" in text
    assert "echo" in text
