"""Tracer API: runs, spans, and events."""

from __future__ import annotations

from types import TracebackType
from typing import Any, Iterable, Literal, Mapping, Self

from sentinel_ai import context as ctx
from sentinel_ai._utils import new_id, omit_none, utc_now_iso
from sentinel_ai._version import SCHEMA_VERSION, SDK_LANGUAGE, SDK_NAME, SDK_VERSION
from sentinel_ai.buffer import BatchBuffer
from sentinel_ai.exporters import Exporter, as_exporter_list

RunStatus = Literal["running", "succeeded", "failed", "cancelled", "timed_out"]
SpanStatus = Literal["ok", "error", "unset"]
SpanKind = Literal["llm", "tool", "planner", "memory", "agent", "custom"]
EventType = Literal["retry", "error", "log", "checkpoint", "feedback", "custom"]
EventLevel = Literal["debug", "info", "warn", "error"]

_TERMINAL_RUN_STATUSES: set[str] = {"succeeded", "failed", "cancelled", "timed_out"}


class SpanHandle:
    """Active or finished span within a run."""

    def __init__(
        self,
        tracer: Tracer,
        *,
        run_id: str,
        span_id: str,
        kind: SpanKind,
        name: str,
        parent_span_id: str | None,
        trace_id: str | None,
        tags: list[str] | None,
        attributes: dict[str, Any] | None,
        llm: dict[str, Any] | None,
        tool: dict[str, Any] | None,
        planner: dict[str, Any] | None,
        memory: dict[str, Any] | None,
        started_at: str,
    ) -> None:
        self._tracer = tracer
        self.run_id = run_id
        self.span_id = span_id
        self.kind = kind
        self.name = name
        self.parent_span_id = parent_span_id
        self.trace_id = trace_id
        self.tags = tags
        self.attributes = attributes
        self.llm = llm
        self.tool = tool
        self.planner = planner
        self.memory = memory
        self.started_at = started_at
        self.status: SpanStatus = "unset"
        self.ended_at: str | None = None
        self.error: dict[str, Any] | None = None
        self._finished = False
        self._token: Any | None = None

    def __enter__(self) -> Self:
        self._token = ctx.set_current_span(self)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc is not None and not self._finished:
            self.end(status="error", error=_error_from_exc(exc))
        elif not self._finished:
            self.end(status="ok")
        if self._token is not None:
            ctx.reset_current_span(self._token)
            self._token = None

    def end(
        self,
        *,
        status: SpanStatus = "ok",
        error: Mapping[str, Any] | None = None,
        attributes: Mapping[str, Any] | None = None,
        llm: Mapping[str, Any] | None = None,
        tool: Mapping[str, Any] | None = None,
        planner: Mapping[str, Any] | None = None,
        memory: Mapping[str, Any] | None = None,
    ) -> None:
        if self._finished:
            return
        self._finished = True
        self.status = status
        self.ended_at = utc_now_iso()
        if error is not None:
            self.error = dict(error)
        if attributes:
            merged = dict(self.attributes or {})
            merged.update(attributes)
            self.attributes = merged
        if llm is not None:
            self.llm = {**(self.llm or {}), **dict(llm)}
        if tool is not None:
            self.tool = {**(self.tool or {}), **dict(tool)}
        if planner is not None:
            self.planner = {**(self.planner or {}), **dict(planner)}
        if memory is not None:
            self.memory = {**(self.memory or {}), **dict(memory)}
        self._tracer._export_span(self)  # noqa: SLF001 — intentional internal hook


class RunHandle:
    """Active or finished run (timeline root)."""

    def __init__(
        self,
        tracer: Tracer,
        *,
        run_id: str,
        trace_id: str,
        name: str | None,
        agent_name: str | None,
        agent_version: str | None,
        config_hash: str | None,
        environment: str | None,
        parent_run_id: str | None,
        tags: list[str] | None,
        attributes: dict[str, Any] | None,
        started_at: str,
    ) -> None:
        self._tracer = tracer
        self.run_id = run_id
        self.trace_id = trace_id
        self.name = name
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.config_hash = config_hash
        self.environment = environment
        self.parent_run_id = parent_run_id
        self.tags = tags
        self.attributes = attributes
        self.started_at = started_at
        self.status: RunStatus = "running"
        self.ended_at: str | None = None
        self.error: dict[str, Any] | None = None
        self._finished = False
        self._token: Any | None = None
        self._root_span: SpanHandle | None = None

    def __enter__(self) -> Self:
        self._token = ctx.set_current_run(self)
        self._tracer._export_run(self, force_status="running")  # noqa: SLF001
        self._root_span = self._tracer.start_span(
            kind="agent",
            name=self.agent_name or self.name or "agent",
            run_id=self.run_id,
            parent_span_id=None,
        )
        self._root_span.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._root_span is not None:
            self._root_span.__exit__(exc_type, exc, tb)
            self._root_span = None
        if exc is not None and not self._finished:
            self.end(status="failed", error=_error_from_exc(exc))
        elif not self._finished:
            self.end(status="succeeded")
        if self._token is not None:
            ctx.reset_current_run(self._token)
            self._token = None

    def end(
        self,
        *,
        status: RunStatus = "succeeded",
        error: Mapping[str, Any] | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> None:
        if self._finished:
            return
        if status == "running":
            raise ValueError("Cannot end a run with status 'running'")
        self._finished = True
        self.status = status
        self.ended_at = utc_now_iso()
        if error is not None:
            self.error = dict(error)
        if attributes:
            merged = dict(self.attributes or {})
            merged.update(attributes)
            self.attributes = merged
        self._tracer._export_run(self)  # noqa: SLF001
        self._tracer.flush()


class Tracer:
    """
    Primary instrumentation entrypoint.

    Example:
        tracer = Tracer(project_id="proj_demo", exporter=FileExporter("out.jsonl"))
        with tracer.start_run(name="task") as run:
            with tracer.start_span(kind="tool", name="search", tool={"tool_name": "search"}):
                ...
    """

    def __init__(
        self,
        *,
        project_id: str,
        exporter: Exporter | Iterable[Exporter] | None = None,
        agent_name: str | None = None,
        agent_version: str | None = None,
        environment: str | None = None,
        default_tags: Iterable[str] | None = None,
        max_batch_size: int = 64,
        flush_interval_seconds: float | None = 2.0,
    ) -> None:
        if not project_id:
            raise ValueError("project_id is required")
        self.project_id = project_id
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.environment = environment
        self.default_tags = list(default_tags or [])
        exporters = as_exporter_list(exporter)
        self._buffer = BatchBuffer(
            project_id=project_id,
            exporters=exporters,
            max_batch_size=max_batch_size,
            flush_interval_seconds=flush_interval_seconds if exporters else None,
        )

    def start_run(
        self,
        *,
        name: str | None = None,
        run_id: str | None = None,
        trace_id: str | None = None,
        agent_name: str | None = None,
        agent_version: str | None = None,
        config_hash: str | None = None,
        environment: str | None = None,
        parent_run_id: str | None = None,
        tags: Iterable[str] | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> RunHandle:
        rid = run_id or new_id("run_")
        return RunHandle(
            self,
            run_id=rid,
            trace_id=trace_id or rid,
            name=name,
            agent_name=agent_name if agent_name is not None else self.agent_name,
            agent_version=agent_version if agent_version is not None else self.agent_version,
            config_hash=config_hash,
            environment=environment if environment is not None else self.environment,
            parent_run_id=parent_run_id,
            tags=_merge_tags(self.default_tags, tags),
            attributes=dict(attributes) if attributes else None,
            started_at=utc_now_iso(),
        )

    def start_span(
        self,
        *,
        kind: SpanKind,
        name: str,
        run_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        trace_id: str | None = None,
        tags: Iterable[str] | None = None,
        attributes: Mapping[str, Any] | None = None,
        llm: Mapping[str, Any] | None = None,
        tool: Mapping[str, Any] | None = None,
        planner: Mapping[str, Any] | None = None,
        memory: Mapping[str, Any] | None = None,
    ) -> SpanHandle:
        if kind == "llm" and llm is None:
            raise ValueError("llm payload is required when kind='llm'")
        if kind == "tool" and tool is None:
            raise ValueError("tool payload is required when kind='tool'")
        if kind == "tool" and "tool_name" not in (tool or {}):
            raise ValueError("tool.tool_name is required when kind='tool'")

        active_run = ctx.get_current_run()
        resolved_run_id = run_id or (active_run.run_id if active_run else None)
        if not resolved_run_id:
            raise RuntimeError("start_span requires an active run or explicit run_id")

        active_span = ctx.get_current_span()
        resolved_parent = parent_span_id
        if resolved_parent is None and active_span is not None:
            resolved_parent = active_span.span_id

        resolved_trace = trace_id or (active_run.trace_id if active_run else resolved_run_id)

        return SpanHandle(
            self,
            run_id=resolved_run_id,
            span_id=span_id or new_id("span_"),
            kind=kind,
            name=name,
            parent_span_id=resolved_parent,
            trace_id=resolved_trace,
            tags=_merge_tags([], tags),
            attributes=dict(attributes) if attributes else None,
            llm=dict(llm) if llm else None,
            tool=dict(tool) if tool else None,
            planner=dict(planner) if planner else None,
            memory=dict(memory) if memory else None,
            started_at=utc_now_iso(),
        )

    def record_event(
        self,
        *,
        type: EventType,
        message: str | None = None,
        run_id: str | None = None,
        span_id: str | None = None,
        event_id: str | None = None,
        level: EventLevel | None = None,
        tags: Iterable[str] | None = None,
        attributes: Mapping[str, Any] | None = None,
        error: Mapping[str, Any] | None = None,
    ) -> str:
        active_run = ctx.get_current_run()
        resolved_run_id = run_id or (active_run.run_id if active_run else None)
        if not resolved_run_id:
            raise RuntimeError("record_event requires an active run or explicit run_id")

        active_span = ctx.get_current_span()
        resolved_span = span_id or (active_span.span_id if active_span else None)
        eid = event_id or new_id("evt_")

        payload = omit_none(
            {
                "schema_version": SCHEMA_VERSION,
                "project_id": self.project_id,
                "run_id": resolved_run_id,
                "event_id": eid,
                "span_id": resolved_span,
                "type": type,
                "timestamp": utc_now_iso(),
                "message": message,
                "level": level,
                "tags": list(tags) if tags else None,
                "attributes": dict(attributes) if attributes else None,
                "error": dict(error) if error else None,
            }
        )
        self._buffer.add_event(payload)
        return eid

    def flush(self) -> None:
        self._buffer.flush()

    def shutdown(self) -> None:
        self._buffer.shutdown()

    # --- internal serialization hooks ---

    def _export_run(self, run: RunHandle, *, force_status: RunStatus | None = None) -> None:
        status = force_status or run.status
        payload = omit_none(
            {
                "schema_version": SCHEMA_VERSION,
                "project_id": self.project_id,
                "run_id": run.run_id,
                "trace_id": run.trace_id,
                "parent_run_id": run.parent_run_id,
                "name": run.name,
                "agent_name": run.agent_name,
                "agent_version": run.agent_version,
                "config_hash": run.config_hash,
                "environment": run.environment,
                "status": status,
                "started_at": run.started_at,
                "ended_at": run.ended_at
                if status in _TERMINAL_RUN_STATUSES
                else None,
                "tags": run.tags,
                "attributes": run.attributes,
                "error": run.error,
                "sdk": {
                    "name": SDK_NAME,
                    "version": SDK_VERSION,
                    "language": SDK_LANGUAGE,
                },
            }
        )
        if status in _TERMINAL_RUN_STATUSES and "ended_at" not in payload:
            payload["ended_at"] = utc_now_iso()
        self._buffer.add_run(payload)

    def _export_span(self, span: SpanHandle) -> None:
        payload = omit_none(
            {
                "schema_version": SCHEMA_VERSION,
                "project_id": self.project_id,
                "run_id": span.run_id,
                "span_id": span.span_id,
                "parent_span_id": span.parent_span_id,
                "trace_id": span.trace_id,
                "kind": span.kind,
                "name": span.name,
                "status": span.status,
                "started_at": span.started_at,
                "ended_at": span.ended_at,
                "tags": span.tags,
                "attributes": span.attributes,
                "error": span.error,
                "llm": span.llm,
                "tool": span.tool,
                "planner": span.planner,
                "memory": span.memory,
            }
        )
        self._buffer.add_span(payload)


def _merge_tags(base: Iterable[str], extra: Iterable[str] | None) -> list[str] | None:
    tags = list(base)
    if extra:
        tags.extend(extra)
    # preserve order, drop dupes
    seen: set[str] = set()
    ordered: list[str] = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            ordered.append(tag)
    return ordered or None


def _error_from_exc(exc: BaseException) -> dict[str, Any]:
    return omit_none(
        {
            "type": type(exc).__name__,
            "message": str(exc),
            "retriable": False,
        }
    )
