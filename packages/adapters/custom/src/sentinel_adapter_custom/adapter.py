"""CustomAgent reference adapter — thin Tracer helpers."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from sentinel_ai import RunHandle, SpanHandle, Tracer
from sentinel_adapter_base import AdapterMetadata


class CustomAdapter:
    """
    Official reference adapter for hand-rolled agents.

    Provides ergonomic span helpers while emitting canonical schema via Tracer.
    """

    def __init__(self, *, adapter_version: str = "0.1.0") -> None:
        self._tracer: Tracer | None = None
        self._adapter_version = adapter_version

    @property
    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            name="sentinel-adapter-custom",
            version=self._adapter_version,
            framework="custom",
            framework_version_range="*",
            capabilities=(
                "run",
                "llm_span",
                "tool_span",
                "planner_span",
                "memory_span",
                "events",
            ),
            description="Reference adapter for hand-rolled agent runtimes",
        )

    def bind(self, tracer: Tracer) -> None:
        self._tracer = tracer

    @property
    def tracer(self) -> Tracer | None:
        return self._tracer

    def _require_tracer(self) -> Tracer:
        if self._tracer is None:
            raise RuntimeError("CustomAdapter.bind(tracer) required before use")
        return self._tracer

    def start_run(
        self,
        *,
        name: str | None = None,
        run_id: str | None = None,
        agent_name: str | None = None,
        agent_version: str | None = None,
        tags: Iterable[str] | None = None,
        attributes: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> RunHandle:
        tracer = self._require_tracer()
        attrs = dict(attributes or {})
        attrs.setdefault(
            "adapter",
            {
                "name": self.metadata.name,
                "version": self.metadata.version,
                "framework": self.metadata.framework,
            },
        )
        return tracer.start_run(
            name=name,
            run_id=run_id,
            agent_name=agent_name,
            agent_version=agent_version,
            tags=tags,
            attributes=attrs,
            **kwargs,
        )

    def llm_span(
        self,
        *,
        name: str = "chat.completions",
        provider: str | None = None,
        model: str | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        llm: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> SpanHandle:
        tracer = self._require_tracer()
        payload: dict[str, Any] = dict(llm or {})
        if provider is not None:
            payload.setdefault("provider", provider)
        if model is not None:
            payload.setdefault("model", model)
        if tokens_in is not None:
            payload.setdefault("tokens_in", tokens_in)
        if tokens_out is not None:
            payload.setdefault("tokens_out", tokens_out)
        if "model" not in payload and "provider" not in payload:
            payload.setdefault("provider", "unknown")
            payload.setdefault("model", "unknown")
        return tracer.start_span(kind="llm", name=name, llm=payload, **kwargs)

    def tool_span(
        self,
        tool_name: str,
        *,
        name: str | None = None,
        input: Mapping[str, Any] | None = None,
        output: Mapping[str, Any] | None = None,
        tool: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> SpanHandle:
        tracer = self._require_tracer()
        payload: dict[str, Any] = dict(tool or {})
        payload["tool_name"] = tool_name
        if input is not None:
            payload.setdefault("input", dict(input))
        if output is not None:
            payload.setdefault("output", dict(output))
        return tracer.start_span(
            kind="tool",
            name=name or tool_name,
            tool=payload,
            **kwargs,
        )

    def planner_span(
        self,
        *,
        name: str = "plan",
        planner_name: str | None = None,
        plan: list[Any] | None = None,
        planner: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> SpanHandle:
        tracer = self._require_tracer()
        payload: dict[str, Any] = dict(planner or {})
        if planner_name is not None:
            payload.setdefault("planner_name", planner_name)
        if plan is not None:
            payload.setdefault("plan", plan)
        return tracer.start_span(kind="planner", name=name, planner=payload or None, **kwargs)

    def memory_span(
        self,
        *,
        name: str = "memory",
        operation: str | None = None,
        store: str | None = None,
        memory: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> SpanHandle:
        tracer = self._require_tracer()
        payload: dict[str, Any] = dict(memory or {})
        if operation is not None:
            payload.setdefault("operation", operation)
        if store is not None:
            payload.setdefault("store", store)
        return tracer.start_span(kind="memory", name=name, memory=payload or None, **kwargs)

    def record_event(self, **kwargs: Any) -> str:
        return self._require_tracer().record_event(**kwargs)
