"""Environment fingerprint helpers for benchmark cells (FR-B03)."""

from __future__ import annotations

import platform
import sys
from typing import Any

from sentinel_server import __version__ as server_version

KNOWN_DIMENSION_KEYS = (
    "model",
    "planner",
    "tools",
    "memory",
    "agent_version",
    "agent_name",
)


def build_environment_fingerprint(
    *,
    run_payload: dict[str, Any],
    provided: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Merge caller-provided fingerprint fields with values derived from the run.

    Derived fields never overwrite explicit caller keys.
    """
    attrs = run_payload.get("attributes") or {}
    if not isinstance(attrs, dict):
        attrs = {}

    derived: dict[str, Any] = {
        "schema_version": run_payload.get("schema_version"),
        "agent_name": run_payload.get("agent_name"),
        "agent_version": run_payload.get("agent_version"),
        "sentinel_server_version": server_version,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "seed": attrs.get("seed"),
        "sdk_version": attrs.get("sdk_version") or attrs.get("sentinel_sdk_version"),
        "adapter_version": attrs.get("adapter_version"),
        "config_hash": attrs.get("config_hash"),
        "git_sha": attrs.get("git_sha"),
    }
    # Drop empty derived values
    fingerprint = {key: value for key, value in derived.items() if value not in (None, "")}
    if provided:
        fingerprint.update({key: value for key, value in provided.items() if value is not None})
    return fingerprint


def normalize_dimensions(dimensions: dict[str, Any] | None) -> dict[str, Any]:
    """Keep a stable, sorted dimension map for grouping."""
    if not dimensions:
        return {}
    cleaned = {
        str(key): value
        for key, value in dimensions.items()
        if value is not None and value != ""
    }
    return dict(sorted(cleaned.items(), key=lambda item: item[0]))


def dimensions_key(dimensions: dict[str, Any]) -> str:
    parts = [f"{key}={dimensions[key]}" for key in sorted(dimensions)]
    return "|".join(parts) if parts else "(default)"


def infer_dimensions_from_run(run_payload: dict[str, Any]) -> dict[str, Any]:
    """Best-effort dimension extraction when the caller omits some keys."""
    attrs = run_payload.get("attributes") or {}
    if not isinstance(attrs, dict):
        attrs = {}
    dims: dict[str, Any] = {}
    if run_payload.get("agent_version"):
        dims["agent_version"] = run_payload["agent_version"]
    if run_payload.get("agent_name"):
        dims["agent_name"] = run_payload["agent_name"]
    for key in ("model", "planner", "memory", "tools"):
        if key in attrs and attrs[key] is not None:
            dims[key] = attrs[key]
    return normalize_dimensions(dims)


def runtime_info() -> dict[str, Any]:
    return {
        "sentinel_server_version": server_version,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
    }
