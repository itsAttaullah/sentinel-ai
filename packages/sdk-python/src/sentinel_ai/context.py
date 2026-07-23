"""ContextVar propagation for current run and span."""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentinel_ai.tracer import RunHandle, SpanHandle

_current_run: ContextVar[RunHandle | None] = ContextVar("sentinel_current_run", default=None)
_current_span: ContextVar[SpanHandle | None] = ContextVar(
    "sentinel_current_span", default=None
)


def get_current_run() -> RunHandle | None:
    return _current_run.get()


def get_current_span() -> SpanHandle | None:
    return _current_span.get()


def set_current_run(run: RunHandle | None) -> Token[RunHandle | None]:
    return _current_run.set(run)


def set_current_span(span: SpanHandle | None) -> Token[SpanHandle | None]:
    return _current_span.set(span)


def reset_current_run(token: Token[RunHandle | None]) -> None:
    _current_run.reset(token)


def reset_current_span(token: Token[SpanHandle | None]) -> None:
    _current_span.reset(token)
