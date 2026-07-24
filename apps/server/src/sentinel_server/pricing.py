"""Model pricing tables for estimated LLM cost."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from sentinel_server.config import get_settings

_PACKAGE_DIR = Path(__file__).resolve().parent
_CANDIDATE_PRICING_PATHS = [
    _PACKAGE_DIR.parents[2] / "pricing" / "default.json",  # apps/server (editable monorepo)
    Path("/pricing/default.json"),  # Docker image layout
]


def _default_pricing() -> dict[str, Any]:
    return {
        "version": "builtin",
        "currency": "USD",
        "models": {
            "*": {"input_per_1m": 1.0, "output_per_1m": 3.0},
        },
    }


@lru_cache
def load_pricing_table(path: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    if path:
        resolved = Path(path)
    elif settings.pricing_path:
        resolved = Path(settings.pricing_path)
    else:
        resolved = next(
            (p for p in _CANDIDATE_PRICING_PATHS if p.is_file()),
            _CANDIDATE_PRICING_PATHS[0],
        )

    if not resolved.is_file():
        return _default_pricing()
    data = json.loads(resolved.read_text(encoding="utf-8"))
    if "models" not in data:
        raise ValueError(f"Pricing file missing 'models': {resolved}")
    data.setdefault("version", resolved.name)
    data.setdefault("currency", "USD")
    return data


def model_key(provider: str | None, model: str | None) -> str:
    prov = (provider or "unknown").strip().lower()
    mod = (model or "unknown").strip().lower()
    return f"{prov}:{mod}"


def lookup_rates(
    pricing: dict[str, Any],
    *,
    provider: str | None,
    model: str | None,
) -> dict[str, float]:
    models = pricing.get("models") or {}
    key = model_key(provider, model)
    rates = models.get(key) or models.get("*") or {"input_per_1m": 0.0, "output_per_1m": 0.0}
    return {
        "input_per_1m": float(rates.get("input_per_1m", 0.0)),
        "output_per_1m": float(rates.get("output_per_1m", 0.0)),
    }


def estimate_llm_cost_usd(
    pricing: dict[str, Any],
    *,
    provider: str | None,
    model: str | None,
    tokens_in: int,
    tokens_out: int,
) -> float:
    rates = lookup_rates(pricing, provider=provider, model=model)
    return (tokens_in / 1_000_000.0) * rates["input_per_1m"] + (
        tokens_out / 1_000_000.0
    ) * rates["output_per_1m"]


def clear_pricing_cache() -> None:
    load_pricing_table.cache_clear()
