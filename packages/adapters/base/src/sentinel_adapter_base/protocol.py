"""Structural protocol for Sentinel adapters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from sentinel_ai import Tracer

from sentinel_adapter_base.metadata import AdapterMetadata


@runtime_checkable
class AdapterProtocol(Protocol):
    """
    Minimal adapter contract.

    Adapters wrap or drive a ``Tracer``; they must not invent a parallel
    persistence model (ADR-0001 / ADR-0007).
    """

    @property
    def metadata(self) -> AdapterMetadata:
        """Stable identity for conformance and discovery."""

    def bind(self, tracer: Tracer) -> None:
        """Attach this adapter to a Tracer instance."""

    @property
    def tracer(self) -> Tracer | None:
        """Currently bound tracer, if any."""
