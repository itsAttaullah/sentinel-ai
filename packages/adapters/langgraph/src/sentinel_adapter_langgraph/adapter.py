"""Map LangGraph/LangChain-style events onto a Sentinel Tracer."""

from __future__ import annotations

from typing import Any, Mapping

from sentinel_ai import RunHandle, SpanHandle, Tracer
from sentinel_adapter_base import AdapterMetadata


class LangGraphAdapter:
    """
    Adapter that consumes normalized callback-like events.

    Event ``type`` values:
      chain_start / chain_end
      llm_start / llm_end
      tool_start / tool_end
      retry / error
    """

    def __init__(self, *, adapter_version: str = "0.1.0") -> None:
        self._tracer: Tracer | None = None
        self._adapter_version = adapter_version
        self._run: RunHandle | None = None
        self._run_token: Any | None = None
        self._spans: dict[str, SpanHandle] = {}
        self._span_tokens: dict[str, Any] = {}
        self._root_entered = False

    @property
    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            name="sentinel-adapter-langgraph",
            version=self._adapter_version,
            framework="langgraph",
            framework_version_range=">=0.2,<1",
            capabilities=(
                "callback_events",
                "llm_span",
                "tool_span",
                "chain_span",
                "optional_langchain_handler",
            ),
            description="LangGraph / LangChain callback adapter",
        )

    def bind(self, tracer: Tracer) -> None:
        self._tracer = tracer

    @property
    def tracer(self) -> Tracer | None:
        return self._tracer

    def _require_tracer(self) -> Tracer:
        if self._tracer is None:
            raise RuntimeError("LangGraphAdapter.bind(tracer) required before use")
        return self._tracer

    def start_run(
        self,
        *,
        name: str | None = "langgraph-run",
        agent_name: str | None = "langgraph",
        agent_version: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> RunHandle:
        """Begin a Sentinel run; call before feeding events (or let chain_start do it)."""
        if self._run is not None:
            return self._run
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
        run = tracer.start_run(
            name=name,
            agent_name=agent_name,
            agent_version=agent_version,
            attributes=attrs,
            tags=["adapter:langgraph"],
        )
        # Enter run context without auto-creating nested confusion —
        # RunHandle.__enter__ creates root agent span which we keep.
        from sentinel_ai import context as ctx

        self._run_token = ctx.set_current_run(run)
        tracer._export_run(run, force_status="running")  # noqa: SLF001
        root = tracer.start_span(
            kind="agent",
            name=agent_name or name or "langgraph",
            run_id=run.run_id,
            parent_span_id=None,
        )
        self._span_tokens[root.span_id] = ctx.set_current_span(root)
        self._spans["__root__"] = root
        self._root_entered = True
        self._run = run
        return run

    def end_run(self, *, status: str = "succeeded", error: Mapping[str, Any] | None = None) -> None:
        if self._run is None:
            return
        # Close open spans LIFO by ending non-root first
        for key in list(self._spans.keys()):
            if key == "__root__":
                continue
            self._end_span_key(key, status="ok")
        if "__root__" in self._spans:
            self._end_span_key("__root__", status="ok" if status == "succeeded" else "error")
        from sentinel_ai import context as ctx

        if error is not None:
            self._run.end(status=status, error=error)  # type: ignore[arg-type]
        else:
            self._run.end(status=status)  # type: ignore[arg-type]
        if self._run_token is not None:
            ctx.reset_current_run(self._run_token)
            self._run_token = None
        self._run = None
        self._root_entered = False

    def handle_event(self, event: Mapping[str, Any]) -> None:
        """Process one normalized callback event."""
        event_type = str(event.get("type") or "")
        if self._run is None and event_type.endswith("_start"):
            self.start_run(name=str(event.get("name") or "langgraph-run"))

        if event_type == "chain_start":
            self._start_span(
                key=str(event.get("run_id") or event.get("name") or "chain"),
                kind="custom",
                name=str(event.get("name") or "chain"),
                parent_key=str(event["parent_run_id"]) if event.get("parent_run_id") else "__root__",
                attributes={"langgraph_event": "chain_start"},
            )
        elif event_type == "chain_end":
            self._end_span_key(str(event.get("run_id") or event.get("name") or "chain"))
        elif event_type == "llm_start":
            llm: dict[str, Any] = {
                "provider": event.get("provider") or "unknown",
                "model": event.get("model") or "unknown",
            }
            if event.get("messages") is not None:
                llm["messages"] = event["messages"]
            self._start_span(
                key=str(event.get("run_id") or "llm"),
                kind="llm",
                name=str(event.get("name") or "llm"),
                parent_key=str(event["parent_run_id"]) if event.get("parent_run_id") else "__root__",
                llm=llm,
            )
        elif event_type == "llm_end":
            key = str(event.get("run_id") or "llm")
            extra_llm: dict[str, Any] = {}
            if event.get("tokens_in") is not None:
                extra_llm["tokens_in"] = event["tokens_in"]
            if event.get("tokens_out") is not None:
                extra_llm["tokens_out"] = event["tokens_out"]
            if event.get("response") is not None:
                extra_llm["response"] = event["response"]
            self._end_span_key(key, status="ok", llm=extra_llm or None)
        elif event_type == "tool_start":
            tool_name = str(event.get("tool_name") or event.get("name") or "tool")
            tool: dict[str, Any] = {"tool_name": tool_name}
            if event.get("input") is not None:
                tool["input"] = event["input"]
            self._start_span(
                key=str(event.get("run_id") or tool_name),
                kind="tool",
                name=tool_name,
                parent_key=str(event["parent_run_id"]) if event.get("parent_run_id") else "__root__",
                tool=tool,
            )
        elif event_type == "tool_end":
            key = str(event.get("run_id") or event.get("tool_name") or event.get("name") or "tool")
            extra_tool = {"output": event["output"]} if event.get("output") is not None else None
            self._end_span_key(key, status="ok", tool=extra_tool)
        elif event_type == "retry":
            tracer = self._require_tracer()
            tracer.record_event(
                type="retry",
                message=str(event.get("message") or "retry"),
                level="warn",
                attributes=dict(event.get("attributes") or {}),
            )
        elif event_type == "error":
            tracer = self._require_tracer()
            err = event.get("error") or {
                "type": str(event.get("error_type") or "Error"),
                "message": str(event.get("message") or "error"),
            }
            tracer.record_event(
                type="error",
                message=str(event.get("message") or err.get("message")),
                level="error",
                error=dict(err) if isinstance(err, Mapping) else {"message": str(err)},
            )
            key = event.get("run_id")
            if key and str(key) in self._spans:
                self._end_span_key(str(key), status="error", error=dict(err) if isinstance(err, Mapping) else None)

    def as_callback_handler(self) -> Any:
        """
        Return a langchain_core ``BaseCallbackHandler`` when available.

        Raises ``ImportError`` if ``langchain-core`` is not installed.
        """
        try:
            from sentinel_adapter_langgraph.callback import SentinelLangGraphCallback
        except ImportError as exc:  # pragma: no cover - exercised when extra missing
            raise ImportError(
                "langchain-core is required for as_callback_handler(); "
                "pip install 'sentinel-adapter-langgraph[langchain]'"
            ) from exc
        return SentinelLangGraphCallback(self)

    def _start_span(
        self,
        *,
        key: str,
        kind: str,
        name: str,
        parent_key: str | None,
        llm: dict[str, Any] | None = None,
        tool: dict[str, Any] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> SpanHandle:
        from sentinel_ai import context as ctx

        tracer = self._require_tracer()
        if self._run is None:
            self.start_run()
        parent_span_id = None
        if parent_key and parent_key in self._spans:
            parent_span_id = self._spans[parent_key].span_id
        span = tracer.start_span(
            kind=kind,  # type: ignore[arg-type]
            name=name,
            parent_span_id=parent_span_id,
            llm=llm,
            tool=tool,
            attributes=attributes,
        )
        self._span_tokens[span.span_id] = ctx.set_current_span(span)
        self._spans[key] = span
        return span

    def _end_span_key(
        self,
        key: str,
        *,
        status: str = "ok",
        llm: Mapping[str, Any] | None = None,
        tool: Mapping[str, Any] | None = None,
        error: Mapping[str, Any] | None = None,
    ) -> None:
        from sentinel_ai import context as ctx

        span = self._spans.pop(key, None)
        if span is None:
            return
        token = self._span_tokens.pop(span.span_id, None)
        span.end(
            status=status,  # type: ignore[arg-type]
            llm=llm,
            tool=tool,
            error=error,
        )
        if token is not None:
            ctx.reset_current_span(token)
