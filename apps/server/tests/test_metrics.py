"""Unit tests for metrics derivation (no database)."""

from __future__ import annotations

from sentinel_server.pricing import clear_pricing_cache, estimate_llm_cost_usd, load_pricing_table
from sentinel_server.services.metrics import compute_metrics_from_entities


def test_compute_metrics_hello_shape() -> None:
    clear_pricing_cache()
    run = {
        "status": "succeeded",
        "started_at": "2026-07-23T09:15:30.000Z",
        "ended_at": "2026-07-23T09:15:32.500Z",
    }
    spans = [
        {
            "kind": "agent",
            "status": "ok",
            "started_at": "2026-07-23T09:15:30.000Z",
            "ended_at": "2026-07-23T09:15:32.500Z",
        },
        {
            "kind": "llm",
            "status": "ok",
            "started_at": "2026-07-23T09:15:30.100Z",
            "ended_at": "2026-07-23T09:15:31.800Z",
            "llm": {
                "provider": "openai",
                "model": "gpt-4.1-mini",
                "tokens_in": 120,
                "tokens_out": 45,
            },
        },
        {
            "kind": "tool",
            "status": "ok",
            "started_at": "2026-07-23T09:15:31.850Z",
            "ended_at": "2026-07-23T09:15:32.200Z",
            "tool": {"tool_name": "web_search"},
        },
    ]
    events = [{"type": "retry"}, {"type": "log"}]

    metrics = compute_metrics_from_entities(run=run, spans=spans, events=events)
    assert metrics["wall_ms"] == 2500.0
    assert metrics["attribution_ms"]["llm"] == 1700.0
    assert metrics["attribution_ms"]["tool"] == 350.0
    assert metrics["tokens"]["in"] == 120
    assert metrics["tokens"]["out"] == 45
    assert metrics["retry_count"] == 1
    assert metrics["estimated_cost_usd"] > 0
    assert metrics["span_counts"]["llm"] == 1
    assert metrics["status"] == "succeeded"


def test_pricing_fallback_unknown_model() -> None:
    clear_pricing_cache()
    pricing = load_pricing_table()
    cost = estimate_llm_cost_usd(
        pricing,
        provider="acme",
        model="mystery",
        tokens_in=1_000_000,
        tokens_out=0,
    )
    assert cost == float(pricing["models"]["*"]["input_per_1m"])
