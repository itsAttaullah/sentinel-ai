"""Shared plugin surface for Sentinel framework adapters."""

from __future__ import annotations

from sentinel_adapter_base.metadata import AdapterMetadata
from sentinel_adapter_base.protocol import AdapterProtocol
from sentinel_adapter_base.registry import (
    discover_adapters,
    get_adapter_entry_points,
    load_adapter,
)

__all__ = [
    "AdapterMetadata",
    "AdapterProtocol",
    "discover_adapters",
    "get_adapter_entry_points",
    "load_adapter",
]

__version__ = "0.1.0"
