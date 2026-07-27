"""Optional LangChain BaseCallbackHandler bridge."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from sentinel_adapter_langgraph.adapter import LangGraphAdapter


class SentinelLangGraphCallback(BaseCallbackHandler):
    """Translate LangChain callback hooks into ``LangGraphAdapter.handle_event``."""

    def __init__(self, adapter: LangGraphAdapter) -> None:
        super().__init__()
        self.adapter = adapter

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self.adapter.handle_event(
            {
                "type": "chain_start",
                "name": serialized.get("name") or kwargs.get("name") or "chain",
                "run_id": str(run_id),
                "parent_run_id": str(parent_run_id) if parent_run_id else None,
                "input": inputs,
            }
        )

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self.adapter.handle_event(
            {"type": "chain_end", "run_id": str(run_id), "output": outputs}
        )

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        invocation = kwargs.get("invocation_params") or {}
        self.adapter.handle_event(
            {
                "type": "llm_start",
                "name": serialized.get("name") or "llm",
                "run_id": str(run_id),
                "parent_run_id": str(parent_run_id) if parent_run_id else None,
                "model": invocation.get("model") or invocation.get("model_name") or "unknown",
                "provider": invocation.get("provider") or "langchain",
                "messages": [{"role": "user", "content": p} for p in prompts],
            }
        )

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        tokens_in = None
        tokens_out = None
        if response.llm_output and isinstance(response.llm_output, dict):
            usage = response.llm_output.get("token_usage") or {}
            tokens_in = usage.get("prompt_tokens")
            tokens_out = usage.get("completion_tokens")
        text = ""
        if response.generations and response.generations[0]:
            text = getattr(response.generations[0][0], "text", "") or ""
        self.adapter.handle_event(
            {
                "type": "llm_end",
                "run_id": str(run_id),
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "response": {"role": "assistant", "content": text} if text else None,
            }
        )

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self.adapter.handle_event(
            {
                "type": "tool_start",
                "name": serialized.get("name") or "tool",
                "tool_name": serialized.get("name") or "tool",
                "run_id": str(run_id),
                "parent_run_id": str(parent_run_id) if parent_run_id else None,
                "input": {"input": input_str},
            }
        )

    def on_tool_end(self, output: str, *, run_id: UUID, **kwargs: Any) -> None:
        self.adapter.handle_event(
            {
                "type": "tool_end",
                "run_id": str(run_id),
                "output": {"output": output},
            }
        )

    def on_tool_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        self.adapter.handle_event(
            {
                "type": "error",
                "run_id": str(run_id),
                "message": str(error),
                "error": {"type": type(error).__name__, "message": str(error)},
            }
        )
