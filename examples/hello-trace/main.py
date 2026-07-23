"""Minimal Sentinel AI instrumentation example (file export)."""

from __future__ import annotations

import sys
from pathlib import Path

from sentinel_ai import FileExporter, Tracer


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else Path(__file__).parent / "out" / "traces.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)

    tracer = Tracer(
        project_id="proj_demo",
        exporter=FileExporter(out),
        agent_name="demo-agent",
        agent_version="0.1.0",
        environment="dev",
        default_tags=["hello-trace"],
        flush_interval_seconds=None,
    )

    with tracer.start_run(
        name="answer-user-question",
        config_hash="cfg_demo",
        attributes={"task": "What is Sentinel AI?"},
    ) as run:
        with tracer.start_span(
            kind="planner",
            name="plan_next_step",
            planner={
                "planner_name": "react",
                "step_index": 0,
                "plan": ["search", "synthesize", "answer"],
            },
        ):
            pass

        with tracer.start_span(
            kind="llm",
            name="chat.completions",
            llm={
                "provider": "openai",
                "model": "gpt-4.1-mini",
                "tokens_in": 120,
                "tokens_out": 45,
                "tokens_total": 165,
                "temperature": 0.2,
                "finish_reason": "stop",
                "messages": [{"role": "user", "content": "What is Sentinel AI?"}],
                "response": {
                    "role": "assistant",
                    "content": "Sentinel AI observes and evaluates autonomous agents.",
                },
            },
        ):
            pass

        with tracer.start_span(
            kind="tool",
            name="web_search",
            tool={
                "tool_name": "web_search",
                "tool_version": "1",
                "input": {"query": "Sentinel AI agent observability"},
                "output": {"hits": 1},
            },
        ):
            tracer.record_event(
                type="retry",
                message="Transient tool timeout; retrying",
                level="warn",
                attributes={"attempt": 2, "max_attempts": 3},
            )

        with tracer.start_span(
            kind="memory",
            name="memory.write",
            memory={
                "operation": "write",
                "store": "episodic",
                "key": "last_answer",
                "namespace": "demo",
            },
        ):
            pass

    tracer.shutdown()
    print(f"Wrote traces for run_id={run.run_id}")
    print(f"Output: {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
