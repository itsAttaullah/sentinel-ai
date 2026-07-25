"""ORM models for projects, traces, and quarantine."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON

# JSONB on Postgres; JSON elsewhere (e.g. local SQLite tests)
JsonType = JSON().with_variant(JSONB(), "postgresql")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (
        UniqueConstraint("project_id", "run_id", name="uq_runs_project_run"),
        Index("ix_runs_project_started", "project_id", "started_at"),
        Index("ix_runs_project_status", "project_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    agent_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    agent_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tags: Mapped[list | None] = mapped_column(JsonType, nullable=True)
    payload: Mapped[dict] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class Span(Base):
    __tablename__ = "spans"
    __table_args__ = (
        UniqueConstraint("project_id", "span_id", name="uq_spans_project_span"),
        Index("ix_spans_project_run", "project_id", "run_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    span_id: Mapped[str] = mapped_column(String(128), nullable=False)
    parent_span_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("project_id", "event_id", name="uq_events_project_event"),
        Index("ix_events_project_run", "project_id", "run_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    span_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class QuarantineItem(Base):
    __tablename__ = "quarantine_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    error_code: Mapped[str] = mapped_column(String(128), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    payload: Mapped[dict | list | None] = mapped_column(JsonType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class RunMetrics(Base):
    """Derived metrics for a run (latency, cost, attribution, retries)."""

    __tablename__ = "run_metrics"
    __table_args__ = (
        UniqueConstraint("project_id", "run_id", name="uq_run_metrics_project_run"),
        Index("ix_run_metrics_project", "project_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    wall_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metrics: Mapped[dict] = mapped_column(JsonType, nullable=False)
    pricing_table_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class Evaluator(Base):
    """Versioned evaluator definition (immutable per version)."""

    __tablename__ = "evaluators"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "evaluator_id", "version", name="uq_evaluators_project_id_ver"
        ),
        Index("ix_evaluators_project", "project_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False)
    evaluator_id: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)  # deterministic | judge
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class Suite(Base):
    """Versioned evaluation suite binding checks to evaluators."""

    __tablename__ = "suites"
    __table_args__ = (
        UniqueConstraint("project_id", "suite_id", "version", name="uq_suites_project_id_ver"),
        Index("ix_suites_project", "project_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False)
    suite_id: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    definition: Mapped[dict] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class EvalJob(Base):
    """One evaluation execution of a suite against a run."""

    __tablename__ = "eval_jobs"
    __table_args__ = (
        Index("ix_eval_jobs_project_run", "project_id", "run_id"),
        Index("ix_eval_jobs_suite", "project_id", "suite_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False)
    suite_id: Mapped[str] = mapped_column(String(128), nullable=False)
    suite_version: Mapped[str] = mapped_column(String(64), nullable=False)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    summary: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Score(Base):
    """Immutable score record for one evaluator on one run (via an eval job)."""

    __tablename__ = "scores"
    __table_args__ = (
        Index("ix_scores_project_run", "project_id", "run_id"),
        Index("ix_scores_eval_job", "eval_job_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    eval_job_id: Mapped[str] = mapped_column(String(64), nullable=False)
    evaluator_id: Mapped[str] = mapped_column(String(128), nullable=False)
    evaluator_version: Mapped[str] = mapped_column(String(64), nullable=False)
    evaluator_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    score_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class BenchmarkSuite(Base):
    """Versioned benchmark suite: tasks + eval suite + sweep dimensions."""

    __tablename__ = "benchmark_suites"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "benchmark_id", "version", name="uq_benchmark_suites_id_ver"
        ),
        Index("ix_benchmark_suites_project", "project_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False)
    benchmark_id: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    definition: Mapped[dict] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class BenchmarkCell(Base):
    """One matrix cell: config dimensions + linked run (+ optional eval)."""

    __tablename__ = "benchmark_cells"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "benchmark_id",
            "benchmark_version",
            "cell_id",
            name="uq_benchmark_cells_cell",
        ),
        Index("ix_benchmark_cells_suite", "project_id", "benchmark_id", "benchmark_version"),
        Index("ix_benchmark_cells_run", "project_id", "run_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False)
    benchmark_id: Mapped[str] = mapped_column(String(128), nullable=False)
    benchmark_version: Mapped[str] = mapped_column(String(64), nullable=False)
    cell_id: Mapped[str] = mapped_column(String(128), nullable=False)
    task_id: Mapped[str] = mapped_column(String(128), nullable=False)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    eval_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dimensions: Mapped[dict] = mapped_column(JsonType, nullable=False)
    environment_fingerprint: Mapped[dict] = mapped_column(JsonType, nullable=False)
    metrics_snapshot: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    scores_summary: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class BenchmarkJob(Base):
    """Comparison / leaderboard report over registered cells."""

    __tablename__ = "benchmark_jobs"
    __table_args__ = (
        Index("ix_benchmark_jobs_project", "project_id", "benchmark_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False)
    benchmark_id: Mapped[str] = mapped_column(String(128), nullable=False)
    benchmark_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    baseline_agent_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    report: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
