"""Official adapter conformance checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from sentinel_ai import SCHEMA_VERSION, Tracer
from sentinel_ai.exporters import Exporter
from sentinel_adapter_base import AdapterMetadata, AdapterProtocol


class _SupportsConformance(Protocol):
    @property
    def metadata(self) -> AdapterMetadata: ...

    def bind(self, tracer: Tracer) -> None: ...

    @property
    def tracer(self) -> Tracer | None: ...


@dataclass
class ConformanceReport:
    adapter_name: str
    passed: bool
    checks: list[dict[str, Any]] = field(default_factory=list)

    def raise_for_failure(self) -> None:
        if not self.passed:
            failed = [c for c in self.checks if not c["passed"]]
            messages = "; ".join(f"{c['id']}: {c['message']}" for c in failed)
            raise AssertionError(f"Adapter conformance failed: {messages}")


class _MemoryExporter(Exporter):
    """Capture export batches for assertions (not a public SDK exporter)."""

    def __init__(self) -> None:
        self.batches: list[dict[str, Any]] = []

    def export(self, batch: dict[str, Any]) -> None:
        self.batches.append(batch)

    @property
    def runs(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for batch in self.batches:
            out.extend(batch.get("runs") or [])
        return out

    @property
    def spans(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for batch in self.batches:
            out.extend(batch.get("spans") or [])
        return out


def run_conformance(
    adapter: _SupportsConformance,
    *,
    exercise: Callable[[_SupportsConformance, Tracer], None] | None = None,
) -> ConformanceReport:
    """
    Run the official adapter quality bar against ``adapter``.

    If ``exercise`` is omitted, a default scenario is chosen based on known
    adapter APIs (``start_run`` helpers or ``handle_event``).
    """
    checks: list[dict[str, Any]] = []
    meta = adapter.metadata

    def check(check_id: str, ok: bool, message: str) -> None:
        checks.append({"id": check_id, "passed": ok, "message": message})

    check(
        "metadata.name",
        bool(meta.name),
        "metadata.name must be non-empty" if not meta.name else "ok",
    )
    check(
        "metadata.version",
        bool(meta.version),
        "metadata.version must be non-empty" if not meta.version else "ok",
    )
    check(
        "metadata.framework",
        bool(meta.framework),
        "metadata.framework must be non-empty" if not meta.framework else "ok",
    )
    check(
        "metadata.framework_version_range",
        bool(meta.framework_version_range),
        "metadata.framework_version_range required"
        if not meta.framework_version_range
        else "ok",
    )
    check(
        "metadata.schema_version",
        meta.schema_version == SCHEMA_VERSION,
        f"schema_version must be {SCHEMA_VERSION}, got {meta.schema_version}",
    )
    check(
        "protocol",
        isinstance(adapter, AdapterProtocol),
        "adapter must satisfy AdapterProtocol",
    )

    exporter = _MemoryExporter()
    tracer = Tracer(
        project_id="proj_conformance",
        exporter=exporter,
        agent_name="conformance-agent",
        agent_version="0.0.0",
        flush_interval_seconds=None,
    )
    adapter.bind(tracer)
    check("bind", adapter.tracer is tracer, "bind(tracer) must set adapter.tracer")

    try:
        if exercise is not None:
            exercise(adapter, tracer)
        else:
            _default_exercise(adapter, tracer)
    except Exception as exc:  # noqa: BLE001
        check("exercise", False, f"exercise raised: {exc}")
    else:
        check("exercise", True, "ok")

    tracer.flush()
    tracer.shutdown()

    runs = exporter.runs
    spans = exporter.spans
    check("emits_run", len(runs) >= 1, f"expected >=1 run, got {len(runs)}")
    check(
        "emits_agent_or_custom_span",
        any(s.get("kind") in {"agent", "custom"} for s in spans),
        "expected an agent or custom root span",
    )
    check(
        "emits_llm_span",
        any(s.get("kind") == "llm" and isinstance(s.get("llm"), dict) for s in spans),
        "expected llm span with llm payload",
    )
    check(
        "emits_tool_span",
        any(
            s.get("kind") == "tool"
            and isinstance(s.get("tool"), dict)
            and s["tool"].get("tool_name")
            for s in spans
        ),
        "expected tool span with tool_name",
    )

    passed = all(c["passed"] for c in checks)
    return ConformanceReport(adapter_name=meta.name, passed=passed, checks=checks)


def _default_exercise(adapter: Any, tracer: Tracer) -> None:
    if hasattr(adapter, "handle_event"):
        adapter.handle_event(
            {"type": "chain_start", "name": "agent", "run_id": "c1"}
        )
        adapter.handle_event(
            {
                "type": "llm_start",
                "name": "model",
                "run_id": "l1",
                "parent_run_id": "c1",
                "model": "gpt-test",
                "provider": "test",
            }
        )
        adapter.handle_event(
            {
                "type": "llm_end",
                "run_id": "l1",
                "tokens_in": 3,
                "tokens_out": 2,
            }
        )
        adapter.handle_event(
            {
                "type": "tool_start",
                "run_id": "t1",
                "parent_run_id": "c1",
                "tool_name": "search",
                "input": {"q": "x"},
            }
        )
        adapter.handle_event(
            {"type": "tool_end", "run_id": "t1", "output": {"hits": 0}}
        )
        adapter.handle_event({"type": "chain_end", "run_id": "c1"})
        adapter.end_run(status="succeeded")
        return

    if hasattr(adapter, "start_run") and hasattr(adapter, "llm_span"):
        with adapter.start_run(name="conformance-run"):
            with adapter.llm_span(provider="test", model="gpt-test", tokens_in=1, tokens_out=1):
                pass
            with adapter.tool_span("search", input={"q": "x"}):
                pass
        return

    raise TypeError(
        "No default exercise for this adapter; pass exercise=... to run_conformance"
    )
