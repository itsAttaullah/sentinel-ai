"""Adapter identity and compatibility metadata (ADR-0007)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from sentinel_ai import SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class AdapterMetadata:
    """Versioned identity for an official or community adapter."""

    name: str
    version: str
    framework: str
    framework_version_range: str
    schema_version: str = SCHEMA_VERSION
    capabilities: Sequence[str] = field(default_factory=tuple)
    description: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "framework": self.framework,
            "framework_version_range": self.framework_version_range,
            "schema_version": self.schema_version,
            "capabilities": list(self.capabilities),
            "description": self.description,
        }
