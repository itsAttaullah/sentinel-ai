"""Unit tests for the Python SDK (no live server required)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sentinel_ai import FileExporter, MultiExporter, Tracer
from sentinel_ai.context import get_current_run, get_current_span


def _read_batches(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_hello_trace_writes_schema_shaped_batch(tmp_path: Path) -> None:
    out = tmp_path / "traces.jsonl"
    tracer = Tracer(
        project_id="proj_demo",
        exporter=FileExporter(out),
        agent_name="demo-agent",
        agent_version="0.1.0",
        flush_interval_seconds=None,
    )

    with tracer.start_run(name="answer-user-question", tags=["smoke"]) as run:
        assert get_current_run() is run
        with tracer.start_span(
            kind="llm",
            name="chat.completions",
            llm={"provider": "openai", "model": "gpt-4.1-mini", "tokens_in": 10, "tokens_out": 5},
        ) as span:
            assert get_current_span() is span
            assert span.parent_span_id is not None  # rooted under agent span

        with tracer.start_span(
            kind="tool",
            name="web_search",
            tool={"tool_name": "web_search", "input": {"query": "Sentinel AI"}},
        ):
            tracer.record_event(type="retry", message="Transient timeout", attributes={"attempt": 2})

    tracer.shutdown()

    batches = _read_batches(out)
    assert batches, "expected at least one flushed batch"
    merged_runs = [r for b in batches for r in b.get("runs", [])]
    merged_spans = [s for b in batches for s in b.get("spans", [])]
    merged_events = [e for b in batches for e in b.get("events", [])]

    assert any(r["run_id"] == run.run_id and r["status"] == "succeeded" for r in merged_runs)
    assert any(r.get("sdk", {}).get("name") == "sentinel-sdk-python" for r in merged_runs)
    kinds = {s["kind"] for s in merged_spans}
    assert "agent" in kinds and "llm" in kinds and "tool" in kinds
    assert any(e["type"] == "retry" for e in merged_events)

    for batch in batches:
        assert batch["schema_version"] == "1.0.0"
        assert batch["project_id"] == "proj_demo"


def test_llm_span_requires_payload() -> None:
    tracer = Tracer(project_id="proj_demo", flush_interval_seconds=None)
    with tracer.start_run(name="x"):
        with pytest.raises(ValueError, match="llm payload"):
            tracer.start_span(kind="llm", name="call")


def test_tool_span_requires_tool_name() -> None:
    tracer = Tracer(project_id="proj_demo", flush_interval_seconds=None)
    with tracer.start_run(name="x"):
        with pytest.raises(ValueError, match="tool_name"):
            tracer.start_span(kind="tool", name="t", tool={"input": {}})


def test_failed_run_on_exception(tmp_path: Path) -> None:
    out = tmp_path / "traces.jsonl"
    tracer = Tracer(
        project_id="proj_demo",
        exporter=FileExporter(out),
        flush_interval_seconds=None,
    )
    with pytest.raises(RuntimeError, match="boom"):
        with tracer.start_run(name="will-fail"):
            raise RuntimeError("boom")
    tracer.shutdown()
    runs = [r for b in _read_batches(out) for r in b.get("runs", [])]
    assert any(r["status"] == "failed" and r.get("error", {}).get("type") == "RuntimeError" for r in runs)


def test_multi_exporter(tmp_path: Path) -> None:
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    tracer = Tracer(
        project_id="proj_demo",
        exporter=MultiExporter([FileExporter(a), FileExporter(b)]),
        flush_interval_seconds=None,
    )
    with tracer.start_run(name="multi"):
        pass
    tracer.shutdown()
    assert a.exists() and b.exists()
    assert _read_batches(a) and _read_batches(b)
