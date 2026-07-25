"""Benchmark suite registry, cell registration, and comparison reports."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from sentinel_server.models import (
    BenchmarkCell,
    BenchmarkJob,
    BenchmarkSuite,
    EvalJob,
    Run,
    RunMetrics,
    Score,
    utc_now,
)
from sentinel_server.services import evaluation as evalsvc
from sentinel_server.services.fingerprint import (
    build_environment_fingerprint,
    dimensions_key,
    infer_dimensions_from_run,
    normalize_dimensions,
)

DEFAULT_DIMENSIONS = ["model", "planner", "tools", "memory", "agent_version"]


def create_benchmark_suite(
    db: Session,
    *,
    project_id: str,
    benchmark_id: str,
    version: str,
    name: str,
    definition: dict[str, Any],
    description: str | None = None,
) -> BenchmarkSuite:
    existing = db.scalar(
        select(BenchmarkSuite).where(
            BenchmarkSuite.project_id == project_id,
            BenchmarkSuite.benchmark_id == benchmark_id,
            BenchmarkSuite.version == version,
        )
    )
    if existing is not None:
        raise ValueError(f"Benchmark suite already exists: {benchmark_id}@{version}")

    tasks = definition.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("definition.tasks must be a non-empty list")
    for index, task in enumerate(tasks):
        if not isinstance(task, dict) or not task.get("task_id"):
            raise ValueError(f"definition.tasks[{index}] requires task_id")

    eval_suite_id = definition.get("eval_suite_id")
    eval_suite_version = definition.get("eval_suite_version")
    if eval_suite_id:
        suite = evalsvc.get_suite(db, project_id, eval_suite_id, eval_suite_version)
        if suite is None:
            raise ValueError(
                f"Unknown eval suite {eval_suite_id}"
                + (f"@{eval_suite_version}" if eval_suite_version else "")
            )
        definition = {
            **definition,
            "eval_suite_version": eval_suite_version or suite.version,
        }

    dimensions = definition.get("dimensions") or DEFAULT_DIMENSIONS
    if not isinstance(dimensions, list) or not all(isinstance(d, str) for d in dimensions):
        raise ValueError("definition.dimensions must be a list of strings")

    definition = {**definition, "dimensions": dimensions}
    row = BenchmarkSuite(
        project_id=project_id,
        benchmark_id=benchmark_id,
        version=version,
        name=name,
        description=description,
        definition=definition,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_benchmark_suites(db: Session, project_id: str) -> list[BenchmarkSuite]:
    return list(
        db.scalars(
            select(BenchmarkSuite)
            .where(BenchmarkSuite.project_id == project_id)
            .order_by(BenchmarkSuite.benchmark_id.asc(), BenchmarkSuite.version.desc())
        ).all()
    )


def get_benchmark_suite(
    db: Session,
    project_id: str,
    benchmark_id: str,
    version: str | None = None,
) -> BenchmarkSuite | None:
    if version:
        return db.scalar(
            select(BenchmarkSuite).where(
                BenchmarkSuite.project_id == project_id,
                BenchmarkSuite.benchmark_id == benchmark_id,
                BenchmarkSuite.version == version,
            )
        )
    return db.scalar(
        select(BenchmarkSuite)
        .where(
            BenchmarkSuite.project_id == project_id,
            BenchmarkSuite.benchmark_id == benchmark_id,
        )
        .order_by(BenchmarkSuite.created_at.desc())
        .limit(1)
    )


def list_cells(
    db: Session,
    project_id: str,
    benchmark_id: str,
    benchmark_version: str | None = None,
) -> list[BenchmarkCell]:
    stmt = select(BenchmarkCell).where(
        BenchmarkCell.project_id == project_id,
        BenchmarkCell.benchmark_id == benchmark_id,
    )
    if benchmark_version:
        stmt = stmt.where(BenchmarkCell.benchmark_version == benchmark_version)
    return list(db.scalars(stmt.order_by(BenchmarkCell.created_at.asc())).all())


def register_cell(
    db: Session,
    *,
    project_id: str,
    benchmark_id: str,
    benchmark_version: str | None = None,
    task_id: str,
    run_id: str,
    dimensions: dict[str, Any] | None = None,
    environment: dict[str, Any] | None = None,
    cell_id: str | None = None,
    eval_job_id: str | None = None,
    run_eval: bool = False,
) -> BenchmarkCell:
    suite = get_benchmark_suite(db, project_id, benchmark_id, benchmark_version)
    if suite is None:
        raise ValueError(f"Benchmark suite not found: {benchmark_id}")

    task_ids = {t.get("task_id") for t in (suite.definition.get("tasks") or [])}
    if task_id not in task_ids:
        raise ValueError(f"Unknown task_id {task_id!r} for benchmark {benchmark_id}")

    run = db.scalar(select(Run).where(Run.project_id == project_id, Run.run_id == run_id))
    if run is None:
        raise ValueError(f"Run not found: {run_id}")

    dims = normalize_dimensions(dimensions) if dimensions else {}
    inferred = infer_dimensions_from_run(run.payload)
    # Caller dimensions win
    dims = normalize_dimensions({**inferred, **dims})

    fingerprint = build_environment_fingerprint(
        run_payload=run.payload, provided=environment
    )

    metrics_row = db.scalar(
        select(RunMetrics).where(
            RunMetrics.project_id == project_id, RunMetrics.run_id == run_id
        )
    )
    metrics_snapshot = metrics_row.metrics if metrics_row else None

    resolved_eval_job_id = eval_job_id
    scores_summary: dict[str, Any] | None = None

    if run_eval and not resolved_eval_job_id:
        eval_suite_id = suite.definition.get("eval_suite_id")
        if not eval_suite_id:
            raise ValueError("run_eval=true requires definition.eval_suite_id")
        job = evalsvc.run_eval_job(
            db,
            project_id=project_id,
            run_id=run_id,
            suite_id=eval_suite_id,
            suite_version=suite.definition.get("eval_suite_version"),
        )
        resolved_eval_job_id = job.id

    if resolved_eval_job_id:
        job = evalsvc.get_eval_job(db, project_id, resolved_eval_job_id)
        if job is None:
            raise ValueError(f"Eval job not found: {resolved_eval_job_id}")
        scores = evalsvc.list_scores_for_job(db, resolved_eval_job_id)
        scores_summary = _summarize_scores(job, scores)

    resolved_cell_id = cell_id or f"cell_{uuid4().hex[:12]}"
    existing = db.scalar(
        select(BenchmarkCell).where(
            BenchmarkCell.project_id == project_id,
            BenchmarkCell.benchmark_id == suite.benchmark_id,
            BenchmarkCell.benchmark_version == suite.version,
            BenchmarkCell.cell_id == resolved_cell_id,
        )
    )
    if existing is not None:
        raise ValueError(f"Cell already exists: {resolved_cell_id}")

    row = BenchmarkCell(
        project_id=project_id,
        benchmark_id=suite.benchmark_id,
        benchmark_version=suite.version,
        cell_id=resolved_cell_id,
        task_id=task_id,
        run_id=run_id,
        eval_job_id=resolved_eval_job_id,
        dimensions=dims,
        environment_fingerprint=fingerprint,
        metrics_snapshot=metrics_snapshot,
        scores_summary=scores_summary,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def build_leaderboard(
    cells: list[BenchmarkCell],
    *,
    baseline_agent_version: str | None = None,
) -> dict[str, Any]:
    """Aggregate cells into a leaderboard + optional pairwise baseline deltas."""
    groups: dict[str, list[BenchmarkCell]] = {}
    for cell in cells:
        key = dimensions_key(cell.dimensions or {})
        groups.setdefault(key, []).append(cell)

    rows: list[dict[str, Any]] = []
    for key, group in groups.items():
        pass_values = [
            1.0 if (c.scores_summary or {}).get("passed") else 0.0
            for c in group
            if c.scores_summary is not None
        ]
        score_values = [
            float((c.scores_summary or {}).get("mean_score"))
            for c in group
            if (c.scores_summary or {}).get("mean_score") is not None
        ]
        wall_values = [
            float((c.metrics_snapshot or {}).get("wall_ms"))
            for c in group
            if (c.metrics_snapshot or {}).get("wall_ms") is not None
        ]
        cost_values = [
            float((c.metrics_snapshot or {}).get("estimated_cost_usd"))
            for c in group
            if (c.metrics_snapshot or {}).get("estimated_cost_usd") is not None
        ]
        dims = group[0].dimensions or {}
        rows.append(
            {
                "dimensions_key": key,
                "dimensions": dims,
                "cell_count": len(group),
                "scored_count": len(pass_values),
                "pass_rate": _mean(pass_values),
                "mean_score": _mean(score_values),
                "mean_wall_ms": _mean(wall_values),
                "mean_cost_usd": _mean(cost_values),
                "task_ids": sorted({c.task_id for c in group}),
                "run_ids": [c.run_id for c in group],
                "fingerprints": [c.environment_fingerprint for c in group],
            }
        )

    rows.sort(
        key=lambda r: (
            -(r["pass_rate"] if r["pass_rate"] is not None else -1.0),
            -(r["mean_score"] if r["mean_score"] is not None else -1.0),
            r["mean_wall_ms"] if r["mean_wall_ms"] is not None else 1e18,
        )
    )
    for index, row in enumerate(rows, start=1):
        row["rank"] = index

    pairwise: list[dict[str, Any]] = []
    baseline_row = None
    if baseline_agent_version:
        for row in rows:
            if str((row["dimensions"] or {}).get("agent_version")) == baseline_agent_version:
                baseline_row = row
                break
        if baseline_row is not None:
            for row in rows:
                if row["dimensions_key"] == baseline_row["dimensions_key"]:
                    continue
                pairwise.append(
                    {
                        "candidate": row["dimensions"],
                        "baseline_agent_version": baseline_agent_version,
                        "delta_pass_rate": _delta(row["pass_rate"], baseline_row["pass_rate"]),
                        "delta_mean_score": _delta(row["mean_score"], baseline_row["mean_score"]),
                        "delta_mean_wall_ms": _delta(
                            row["mean_wall_ms"], baseline_row["mean_wall_ms"]
                        ),
                        "delta_mean_cost_usd": _delta(
                            row["mean_cost_usd"], baseline_row["mean_cost_usd"]
                        ),
                    }
                )

    return {
        "leaderboard": rows,
        "pairwise": pairwise,
        "baseline_agent_version": baseline_agent_version,
        "cell_count": len(cells),
        "group_count": len(rows),
    }


def run_benchmark_job(
    db: Session,
    *,
    project_id: str,
    benchmark_id: str,
    benchmark_version: str | None = None,
    baseline_agent_version: str | None = None,
) -> BenchmarkJob:
    suite = get_benchmark_suite(db, project_id, benchmark_id, benchmark_version)
    if suite is None:
        raise ValueError(f"Benchmark suite not found: {benchmark_id}")

    cells = list_cells(db, project_id, suite.benchmark_id, suite.version)
    job = BenchmarkJob(
        id=f"bench_{uuid4().hex[:16]}",
        project_id=project_id,
        benchmark_id=suite.benchmark_id,
        benchmark_version=suite.version,
        status="running",
        baseline_agent_version=baseline_agent_version,
    )
    db.add(job)
    db.flush()

    try:
        report = build_leaderboard(cells, baseline_agent_version=baseline_agent_version)
        report["benchmark_id"] = suite.benchmark_id
        report["benchmark_version"] = suite.version
        report["name"] = suite.name
        job.report = report
        job.status = "succeeded"
        job.finished_at = utc_now()
        db.commit()
        db.refresh(job)
        return job
    except Exception as exc:  # noqa: BLE001
        job.status = "failed"
        job.error_message = str(exc)
        job.finished_at = utc_now()
        db.commit()
        db.refresh(job)
        return job


def get_benchmark_job(db: Session, project_id: str, job_id: str) -> BenchmarkJob | None:
    return db.scalar(
        select(BenchmarkJob).where(
            BenchmarkJob.project_id == project_id, BenchmarkJob.id == job_id
        )
    )


def suite_to_dict(row: BenchmarkSuite) -> dict[str, Any]:
    return {
        "benchmark_id": row.benchmark_id,
        "version": row.version,
        "name": row.name,
        "description": row.description,
        "definition": row.definition,
        "created_at": row.created_at.isoformat(),
    }


def cell_to_dict(row: BenchmarkCell) -> dict[str, Any]:
    return {
        "cell_id": row.cell_id,
        "benchmark_id": row.benchmark_id,
        "benchmark_version": row.benchmark_version,
        "task_id": row.task_id,
        "run_id": row.run_id,
        "eval_job_id": row.eval_job_id,
        "dimensions": row.dimensions,
        "environment_fingerprint": row.environment_fingerprint,
        "metrics_snapshot": row.metrics_snapshot,
        "scores_summary": row.scores_summary,
        "created_at": row.created_at.isoformat(),
    }


def job_to_dict(row: BenchmarkJob) -> dict[str, Any]:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "benchmark_id": row.benchmark_id,
        "benchmark_version": row.benchmark_version,
        "status": row.status,
        "baseline_agent_version": row.baseline_agent_version,
        "report": row.report,
        "error_message": row.error_message,
        "created_at": row.created_at.isoformat(),
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
    }


def _summarize_scores(job: EvalJob, scores: list[Score]) -> dict[str, Any]:
    values = [s.score_value for s in scores if s.score_value is not None]
    return {
        "eval_job_id": job.id,
        "passed": job.passed,
        "status": job.status,
        "score_count": len(scores),
        "pass_count": sum(1 for s in scores if s.passed),
        "mean_score": _mean([float(v) for v in values]),
    }


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return round(a - b, 6)
