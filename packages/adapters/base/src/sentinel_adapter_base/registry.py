"""Entry-point discovery for ``sentinel.adapters`` plugins."""

from __future__ import annotations

from importlib.metadata import EntryPoint, entry_points
from typing import Any, Callable

ENTRY_POINT_GROUP = "sentinel.adapters"


def get_adapter_entry_points() -> list[EntryPoint]:
    """Return installed adapter entry points (empty if none registered)."""
    selected = entry_points().select(group=ENTRY_POINT_GROUP)
    return list(selected)


def load_adapter(name: str) -> Any:
    """
    Load an adapter factory/class by entry-point name.

    Raises ``KeyError`` when the name is not registered.
    """
    for ep in get_adapter_entry_points():
        if ep.name == name:
            return ep.load()
    raise KeyError(f"No sentinel.adapters entry point named {name!r}")


def discover_adapters() -> dict[str, Callable[..., Any]]:
    """Map entry-point name → loaded callable/class."""
    return {ep.name: ep.load() for ep in get_adapter_entry_points()}
