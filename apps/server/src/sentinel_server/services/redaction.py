"""Payload redaction for ingest and API reads."""

from __future__ import annotations

import copy
import re
from typing import Any, Literal

RedactionMode = Literal["off", "default", "strict"]

_SENSITIVE_KEY = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|credential|private[_-]?key)",
    re.IGNORECASE,
)
_SECRETISH_VALUE = re.compile(
    r"(?i)\b(sk-[a-z0-9]{8,}|bearer\s+[a-z0-9\-._~+/]+=*|ghp_[a-z0-9]{20,})\b"
)

REDACTED = "[REDACTED]"


def redact_ingest_batch(batch: dict[str, Any], *, mode: RedactionMode) -> dict[str, Any]:
    """Return a deep-copied batch with sensitive fields redacted."""
    if mode == "off":
        return batch
    out = copy.deepcopy(batch)
    for run in out.get("runs") or []:
        if isinstance(run, dict):
            _redact_mapping(run.get("attributes"), mode=mode)
    for span in out.get("spans") or []:
        if not isinstance(span, dict):
            continue
        _redact_mapping(span.get("attributes"), mode=mode)
        _redact_llm(span.get("llm"), mode=mode)
        _redact_tool(span.get("tool"), mode=mode)
    for event in out.get("events") or []:
        if isinstance(event, dict):
            _redact_mapping(event.get("attributes"), mode=mode)
            if isinstance(event.get("error"), dict):
                _redact_mapping(event["error"], mode=mode)
    return out


def redact_run_detail(detail: dict[str, Any], *, mode: RedactionMode) -> dict[str, Any]:
    """Redact a run detail payload (run/spans/events)."""
    if mode == "off":
        return detail
    out = copy.deepcopy(detail)
    if isinstance(out.get("run"), dict):
        _redact_mapping(out["run"].get("attributes"), mode=mode)
    for span in out.get("spans") or []:
        if isinstance(span, dict):
            _redact_mapping(span.get("attributes"), mode=mode)
            _redact_llm(span.get("llm"), mode=mode)
            _redact_tool(span.get("tool"), mode=mode)
    for event in out.get("events") or []:
        if isinstance(event, dict):
            _redact_mapping(event.get("attributes"), mode=mode)
    return out


def _redact_mapping(data: Any, *, mode: RedactionMode) -> None:
    if not isinstance(data, dict):
        return
    for key, value in list(data.items()):
        if _SENSITIVE_KEY.search(str(key)):
            data[key] = REDACTED
            continue
        if isinstance(value, dict):
            _redact_mapping(value, mode=mode)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _redact_mapping(item, mode=mode)
                elif isinstance(item, str) and _SECRETISH_VALUE.search(item):
                    # replace in-place is awkward for list; skip
                    pass
        elif isinstance(value, str) and _SECRETISH_VALUE.search(value):
            data[key] = _SECRETISH_VALUE.sub(REDACTED, value)


def _redact_llm(llm: Any, *, mode: RedactionMode) -> None:
    if not isinstance(llm, dict):
        return
    if mode == "strict":
        if "messages" in llm:
            llm["messages"] = REDACTED
        if "response" in llm:
            llm["response"] = REDACTED
        if "prompt" in llm:
            llm["prompt"] = REDACTED
        return
    messages = llm.get("messages")
    if isinstance(messages, list):
        for msg in messages:
            if isinstance(msg, dict) and "content" in msg:
                msg["content"] = REDACTED
    response = llm.get("response")
    if isinstance(response, dict) and "content" in response:
        response["content"] = REDACTED
    elif isinstance(response, str):
        llm["response"] = REDACTED


def _redact_tool(tool: Any, *, mode: RedactionMode) -> None:
    if not isinstance(tool, dict):
        return
    if mode == "strict":
        if "input" in tool:
            tool["input"] = REDACTED
        if "output" in tool:
            tool["output"] = REDACTED
        return
    for field in ("input", "output"):
        value = tool.get(field)
        if isinstance(value, dict):
            _redact_mapping(value, mode=mode)
        elif isinstance(value, str) and _SECRETISH_VALUE.search(value):
            tool[field] = _SECRETISH_VALUE.sub(REDACTED, value)
