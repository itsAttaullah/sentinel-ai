"""Ingest persistence: idempotent upserts + quarantine."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from sentinel_server.models import Event, Project, QuarantineItem, Run, Span
from sentinel_server.services.metrics import recompute_runs
from sentinel_server.timeutil import parse_dt


def ensure_project(db: Session, project_id: str, *, name: str | None = None) -> Project:
    project = db.get(Project, project_id)
    if project is not None:
        return project
    project = Project(id=project_id, name=name or project_id)
    db.add(project)
    db.flush()
    return project


def quarantine(
    db: Session,
    *,
    error_code: str,
    message: str,
    payload: Any,
    details: list | dict | None = None,
    project_id: str | None = None,
) -> QuarantineItem:
    item = QuarantineItem(
        project_id=project_id,
        error_code=error_code,
        message=message,
        details=details if isinstance(details, dict) else {"errors": details},
        payload=payload,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def persist_ingest_batch(db: Session, batch: dict[str, Any]) -> dict[str, int]:
    project_id = batch["project_id"]
    ensure_project(db, project_id)

    runs = batch.get("runs") or []
    spans = batch.get("spans") or []
    events = batch.get("events") or []

    for run in runs:
        _upsert_run(db, run)
    for span in spans:
        _upsert_span(db, span)
    for event in events:
        _upsert_event(db, event)

    db.flush()

    affected_run_ids: set[str] = set()
    for run in runs:
        affected_run_ids.add(run["run_id"])
    for span in spans:
        affected_run_ids.add(span["run_id"])
    for event in events:
        affected_run_ids.add(event["run_id"])

    recompute_runs(db, project_id, affected_run_ids)
    db.commit()
    return {"runs": len(runs), "spans": len(spans), "events": len(events)}


def _upsert_run(db: Session, payload: dict[str, Any]) -> None:
    values = {
        "project_id": payload["project_id"],
        "run_id": payload["run_id"],
        "status": payload["status"],
        "name": payload.get("name"),
        "agent_name": payload.get("agent_name"),
        "agent_version": payload.get("agent_version"),
        "started_at": parse_dt(payload.get("started_at")),
        "ended_at": parse_dt(payload.get("ended_at")),
        "tags": payload.get("tags"),
        "payload": payload,
    }
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        stmt = pg_insert(Run).values(**values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_runs_project_run",
            set_={
                "status": stmt.excluded.status,
                "name": stmt.excluded.name,
                "agent_name": stmt.excluded.agent_name,
                "agent_version": stmt.excluded.agent_version,
                "started_at": stmt.excluded.started_at,
                "ended_at": stmt.excluded.ended_at,
                "tags": stmt.excluded.tags,
                "payload": stmt.excluded.payload,
            },
        )
        db.execute(stmt)
        return

    existing = db.scalar(
        select(Run).where(
            Run.project_id == values["project_id"],
            Run.run_id == values["run_id"],
        )
    )
    if existing is None:
        db.add(Run(**values))
    else:
        for key, value in values.items():
            if key in {"project_id", "run_id"}:
                continue
            setattr(existing, key, value)


def _upsert_span(db: Session, payload: dict[str, Any]) -> None:
    values = {
        "project_id": payload["project_id"],
        "run_id": payload["run_id"],
        "span_id": payload["span_id"],
        "parent_span_id": payload.get("parent_span_id"),
        "kind": payload["kind"],
        "name": payload["name"],
        "status": payload["status"],
        "started_at": parse_dt(payload.get("started_at")),
        "ended_at": parse_dt(payload.get("ended_at")),
        "payload": payload,
    }
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        stmt = pg_insert(Span).values(**values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_spans_project_span",
            set_={
                "run_id": stmt.excluded.run_id,
                "parent_span_id": stmt.excluded.parent_span_id,
                "kind": stmt.excluded.kind,
                "name": stmt.excluded.name,
                "status": stmt.excluded.status,
                "started_at": stmt.excluded.started_at,
                "ended_at": stmt.excluded.ended_at,
                "payload": stmt.excluded.payload,
            },
        )
        db.execute(stmt)
        return

    existing = db.scalar(
        select(Span).where(
            Span.project_id == values["project_id"],
            Span.span_id == values["span_id"],
        )
    )
    if existing is None:
        db.add(Span(**values))
    else:
        for key, value in values.items():
            if key in {"project_id", "span_id"}:
                continue
            setattr(existing, key, value)


def _upsert_event(db: Session, payload: dict[str, Any]) -> None:
    values = {
        "project_id": payload["project_id"],
        "run_id": payload["run_id"],
        "event_id": payload["event_id"],
        "span_id": payload.get("span_id"),
        "type": payload["type"],
        "timestamp": parse_dt(payload.get("timestamp")),
        "payload": payload,
    }
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        stmt = pg_insert(Event).values(**values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_events_project_event",
            set_={
                "run_id": stmt.excluded.run_id,
                "span_id": stmt.excluded.span_id,
                "type": stmt.excluded.type,
                "timestamp": stmt.excluded.timestamp,
                "payload": stmt.excluded.payload,
            },
        )
        db.execute(stmt)
        return

    existing = db.scalar(
        select(Event).where(
            Event.project_id == values["project_id"],
            Event.event_id == values["event_id"],
        )
    )
    if existing is None:
        db.add(Event(**values))
    else:
        for key, value in values.items():
            if key in {"project_id", "event_id"}:
                continue
            setattr(existing, key, value)
