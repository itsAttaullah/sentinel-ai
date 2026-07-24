"""Project and run query helpers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from sentinel_server.models import Event, Project, QuarantineItem, Run, RunMetrics, Span
from sentinel_server.services.metrics import (
    aggregate_project_metrics,
    get_run_metrics,
    recompute_run_metrics,
)


def list_projects(db: Session) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.created_at.desc())).all())


def create_project(
    db: Session,
    *,
    name: str,
    project_id: str | None = None,
    description: str | None = None,
) -> Project:
    pid = project_id or name.lower().replace(" ", "_")[:128]
    existing = db.get(Project, pid)
    if existing is not None:
        raise ValueError(f"Project already exists: {pid}")
    project = Project(id=pid, name=name, description=description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: str) -> Project | None:
    return db.get(Project, project_id)


def list_runs(
    db: Session,
    project_id: str,
    *,
    status: str | None = None,
    agent_version: str | None = None,
    tag: str | None = None,
    limit: int = 50,
) -> list[Run]:
    if db.get(Project, project_id) is None:
        return []

    stmt = select(Run).where(Run.project_id == project_id)
    if status:
        stmt = stmt.where(Run.status == status)
    if agent_version:
        stmt = stmt.where(Run.agent_version == agent_version)
    stmt = stmt.order_by(Run.started_at.desc().nulls_last()).limit(limit)
    runs = list(db.scalars(stmt).all())
    if tag:
        runs = [run for run in runs if run.tags and tag in run.tags]
    return runs


def get_run_detail(
    db: Session,
    project_id: str,
    run_id: str,
    *,
    include_spans: bool = True,
    include_events: bool = True,
    include_metrics: bool = True,
) -> dict | None:
    run = db.scalar(
        select(Run).where(Run.project_id == project_id, Run.run_id == run_id)
    )
    if run is None:
        return None

    detail: dict = {"run": run.payload}
    if include_spans:
        spans = list(
            db.scalars(
                select(Span)
                .where(Span.project_id == project_id, Span.run_id == run_id)
                .order_by(Span.started_at.asc().nulls_last())
            ).all()
        )
        detail["spans"] = [span.payload for span in spans]
    if include_events:
        events = list(
            db.scalars(
                select(Event)
                .where(Event.project_id == project_id, Event.run_id == run_id)
                .order_by(Event.timestamp.asc().nulls_last())
            ).all()
        )
        detail["events"] = [event.payload for event in events]
    if include_metrics:
        detail["metrics"] = get_run_metrics(db, project_id, run_id)
    return detail


def list_run_metric_summaries(
    db: Session, project_id: str, run_ids: list[str]
) -> dict[str, RunMetrics]:
    if not run_ids:
        return {}
    rows = list(
        db.scalars(
            select(RunMetrics).where(
                RunMetrics.project_id == project_id,
                RunMetrics.run_id.in_(run_ids),
            )
        ).all()
    )
    return {row.run_id: row for row in rows}


def project_metrics(db: Session, project_id: str) -> dict:
    return aggregate_project_metrics(db, project_id)


def recompute_metrics_for_run(db: Session, project_id: str, run_id: str) -> dict | None:
    metrics = recompute_run_metrics(db, project_id, run_id)
    if metrics is None:
        return None
    db.commit()
    return metrics


def list_quarantine(db: Session, *, limit: int = 50) -> list[QuarantineItem]:
    return list(
        db.scalars(
            select(QuarantineItem).order_by(QuarantineItem.created_at.desc()).limit(limit)
        ).all()
    )
