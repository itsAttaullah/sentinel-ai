"""Derive run metrics: latency, tokens, cost, retries, attribution."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from sentinel_server.models import Event, Run, RunMetrics, Span, utc_now
from sentinel_server.pricing import estimate_llm_cost_usd, load_pricing_table, model_key
from sentinel_server.timeutil import parse_dt

_KIND_KEYS = ("llm", "tool", "planner", "memory", "agent", "custom")


def _duration_ms(started: datetime | None, ended: datetime | None) -> float | None:
    if started is None or ended is None:
        return None
    return max(0.0, (ended - started).total_seconds() * 1000.0)


def compute_metrics_from_entities(
    *,
    run: dict[str, Any],
    spans: list[dict[str, Any]],
    events: list[dict[str, Any]],
    pricing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pure function used by workers/tests — no DB access."""
    pricing = pricing or load_pricing_table()

    started = run.get("started_at")
    ended = run.get("ended_at")
    if isinstance(started, str):
        started = parse_dt(started)
    if isinstance(ended, str):
        ended = parse_dt(ended)

    wall_ms = _duration_ms(started, ended)

    attribution_ms = {kind: 0.0 for kind in _KIND_KEYS}
    span_counts = {kind: 0 for kind in _KIND_KEYS}
    span_error_count = 0
    tokens_in = 0
    tokens_out = 0
    cost_by_model: dict[str, dict[str, Any]] = {}
    estimated_cost = 0.0

    for span in spans:
        kind = span.get("kind") or "custom"
        if kind not in attribution_ms:
            kind = "custom"
        span_counts[kind] = span_counts.get(kind, 0) + 1

        s_start = span.get("started_at")
        s_end = span.get("ended_at")
        if isinstance(s_start, str):
            s_start = parse_dt(s_start)
        if isinstance(s_end, str):
            s_end = parse_dt(s_end)
        dur = _duration_ms(s_start, s_end)
        if dur is not None:
            attribution_ms[kind] += dur

        if span.get("status") == "error":
            span_error_count += 1

        if kind == "llm":
            llm = span.get("llm") or {}
            tin = int(llm.get("tokens_in") or 0)
            tout = int(llm.get("tokens_out") or 0)
            if llm.get("tokens_total") is not None and tin == 0 and tout == 0:
                # best-effort if only total provided
                tin = int(llm.get("tokens_total") or 0)
            tokens_in += tin
            tokens_out += tout
            provider = llm.get("provider")
            model = llm.get("model")
            cost = estimate_llm_cost_usd(
                pricing,
                provider=provider,
                model=model,
                tokens_in=tin,
                tokens_out=tout,
            )
            estimated_cost += cost
            key = model_key(provider, model)
            bucket = cost_by_model.setdefault(
                key,
                {
                    "provider": provider,
                    "model": model,
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "estimated_cost_usd": 0.0,
                    "span_count": 0,
                },
            )
            bucket["tokens_in"] += tin
            bucket["tokens_out"] += tout
            bucket["estimated_cost_usd"] += cost
            bucket["span_count"] += 1

    retry_count = sum(1 for event in events if event.get("type") == "retry")
    error_event_count = sum(1 for event in events if event.get("type") == "error")

    span_total_ms = sum(attribution_ms.values())
    attribution_share = {
        kind: (attribution_ms[kind] / span_total_ms if span_total_ms > 0 else 0.0)
        for kind in _KIND_KEYS
    }

    # Round money for stable API output
    estimated_cost = round(estimated_cost, 8)
    for bucket in cost_by_model.values():
        bucket["estimated_cost_usd"] = round(float(bucket["estimated_cost_usd"]), 8)

    return {
        "wall_ms": round(wall_ms, 3) if wall_ms is not None else None,
        "span_total_ms": round(span_total_ms, 3),
        "attribution_ms": {k: round(v, 3) for k, v in attribution_ms.items()},
        "attribution_share": {k: round(v, 6) for k, v in attribution_share.items()},
        "tokens": {
            "in": tokens_in,
            "out": tokens_out,
            "total": tokens_in + tokens_out,
        },
        "estimated_cost_usd": estimated_cost,
        "cost_by_model": sorted(cost_by_model.values(), key=lambda x: x["estimated_cost_usd"], reverse=True),
        "retry_count": retry_count,
        "error_event_count": error_event_count,
        "span_counts": span_counts,
        "span_error_count": span_error_count,
        "status": run.get("status"),
        "pricing_table_version": pricing.get("version"),
        "currency": pricing.get("currency", "USD"),
        "computed_at": datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "notes": [
            "estimated_cost_usd is an estimate from the configured pricing table",
            "attribution_ms sums span durations by kind (overlaps may double-count)",
        ],
    }


def recompute_run_metrics(db: Session, project_id: str, run_id: str) -> dict[str, Any] | None:
    run = db.scalar(
        select(Run).where(Run.project_id == project_id, Run.run_id == run_id)
    )
    if run is None:
        return None

    spans = list(
        db.scalars(
            select(Span).where(Span.project_id == project_id, Span.run_id == run_id)
        ).all()
    )
    events = list(
        db.scalars(
            select(Event).where(Event.project_id == project_id, Event.run_id == run_id)
        ).all()
    )

    metrics = compute_metrics_from_entities(
        run=run.payload,
        spans=[s.payload for s in spans],
        events=[e.payload for e in events],
    )
    _upsert_run_metrics(db, project_id, run_id, metrics)
    return metrics


def recompute_runs(db: Session, project_id: str, run_ids: set[str]) -> int:
    count = 0
    for run_id in sorted(run_ids):
        if recompute_run_metrics(db, project_id, run_id) is not None:
            count += 1
    return count


def _upsert_run_metrics(
    db: Session, project_id: str, run_id: str, metrics: dict[str, Any]
) -> None:
    values = {
        "project_id": project_id,
        "run_id": run_id,
        "status": metrics.get("status"),
        "wall_ms": metrics.get("wall_ms"),
        "estimated_cost_usd": metrics.get("estimated_cost_usd"),
        "tokens_in": int((metrics.get("tokens") or {}).get("in") or 0),
        "tokens_out": int((metrics.get("tokens") or {}).get("out") or 0),
        "retry_count": int(metrics.get("retry_count") or 0),
        "metrics": metrics,
        "pricing_table_version": metrics.get("pricing_table_version"),
        "computed_at": utc_now(),
    }
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        stmt = pg_insert(RunMetrics).values(**values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_run_metrics_project_run",
            set_={
                "status": stmt.excluded.status,
                "wall_ms": stmt.excluded.wall_ms,
                "estimated_cost_usd": stmt.excluded.estimated_cost_usd,
                "tokens_in": stmt.excluded.tokens_in,
                "tokens_out": stmt.excluded.tokens_out,
                "retry_count": stmt.excluded.retry_count,
                "metrics": stmt.excluded.metrics,
                "pricing_table_version": stmt.excluded.pricing_table_version,
                "computed_at": stmt.excluded.computed_at,
            },
        )
        db.execute(stmt)
        return

    existing = db.scalar(
        select(RunMetrics).where(
            RunMetrics.project_id == project_id,
            RunMetrics.run_id == run_id,
        )
    )
    if existing is None:
        db.add(RunMetrics(**values))
    else:
        for key, value in values.items():
            if key in {"project_id", "run_id"}:
                continue
            setattr(existing, key, value)


def get_run_metrics(db: Session, project_id: str, run_id: str) -> dict[str, Any] | None:
    row = db.scalar(
        select(RunMetrics).where(
            RunMetrics.project_id == project_id,
            RunMetrics.run_id == run_id,
        )
    )
    return row.metrics if row else None


def aggregate_project_metrics(db: Session, project_id: str) -> dict[str, Any]:
    rows = list(
        db.scalars(select(RunMetrics).where(RunMetrics.project_id == project_id)).all()
    )
    run_count = len(rows)
    if run_count == 0:
        return {
            "project_id": project_id,
            "run_count": 0,
            "success_count": 0,
            "success_rate": None,
            "wall_ms": {"avg": None, "p50": None, "p95": None},
            "total_estimated_cost_usd": 0.0,
            "total_tokens": {"in": 0, "out": 0, "total": 0},
            "total_retries": 0,
            "attribution_ms_total": {kind: 0.0 for kind in _KIND_KEYS},
        }

    success_count = sum(1 for row in rows if row.status == "succeeded")
    walls = sorted(row.wall_ms for row in rows if row.wall_ms is not None)
    total_cost = sum(float(row.estimated_cost_usd or 0.0) for row in rows)
    tokens_in = sum(row.tokens_in for row in rows)
    tokens_out = sum(row.tokens_out for row in rows)
    retries = sum(row.retry_count for row in rows)

    attribution_total = {kind: 0.0 for kind in _KIND_KEYS}
    for row in rows:
        attr = (row.metrics or {}).get("attribution_ms") or {}
        for kind in _KIND_KEYS:
            attribution_total[kind] += float(attr.get(kind) or 0.0)

    return {
        "project_id": project_id,
        "run_count": run_count,
        "success_count": success_count,
        "success_rate": round(success_count / run_count, 6),
        "wall_ms": {
            "avg": round(sum(walls) / len(walls), 3) if walls else None,
            "p50": _percentile(walls, 0.50),
            "p95": _percentile(walls, 0.95),
        },
        "total_estimated_cost_usd": round(total_cost, 8),
        "total_tokens": {
            "in": tokens_in,
            "out": tokens_out,
            "total": tokens_in + tokens_out,
        },
        "total_retries": retries,
        "attribution_ms_total": {k: round(v, 3) for k, v in attribution_total.items()},
    }


def _percentile(sorted_values: list[float], pct: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return round(sorted_values[0], 3)
    idx = int(round((len(sorted_values) - 1) * pct))
    idx = min(max(idx, 0), len(sorted_values) - 1)
    return round(sorted_values[idx], 3)
