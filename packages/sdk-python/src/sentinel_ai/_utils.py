"""Shared helpers for IDs and timestamps."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def new_id(prefix: str = "") -> str:
    """Return a compact unique ID. Optional prefix aids readability in fixtures."""
    body = uuid4().hex
    return f"{prefix}{body}" if prefix else body


def utc_now_iso() -> str:
    """RFC 3339 UTC timestamp with Z suffix."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def omit_none(data: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose values are None (keeps empty containers)."""
    return {key: value for key, value in data.items() if value is not None}
