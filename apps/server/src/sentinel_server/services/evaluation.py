"""Evaluator/suite registry and eval job execution."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from sentinel_server.models import (
    EvalJob,
    Evaluator,
    Event,
    Run,
    RunMetrics,
    Score,
    Span,
    Suite,
    utc_now,
)
from sentinel_server.services.eval_engine import (
    EvaluationError,
    apply_threshold,
    evaluate_deterministic,
    evaluate_judge,
    run_context,
)


def create_evaluator(
    db: Session,
    *,
    project_id: str,
    evaluator_id: str,
    version: str,
    kind: str,
    name: str,
    config: dict[str, Any],
    description: str | None = None,
) -> Evaluator:
    if kind not in {"deterministic", "judge"}:
        raise ValueError("kind must be 'deterministic' or 'judge'")
    existing = db.scalar(
        select(Evaluator).where(
            Evaluator.project_id == project_id,
            Evaluator.evaluator_id == evaluator_id,
            Evaluator.version == version,
        )
    )
    if existing is not None:
        raise ValueError(
            f"Evaluator already exists: {evaluator_id}@{version} (versions are immutable)"
        )
    # Validate config early
    _validate_evaluator_config(kind, config)
    row = Evaluator(
        project_id=project_id,
        evaluator_id=evaluator_id,
        version=version,
        kind=kind,
        name=name,
        description=description,
        config=config,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_evaluators(db: Session, project_id: str) -> list[Evaluator]:
    return list(
        db.scalars(
            select(Evaluator)
            .where(Evaluator.project_id == project_id)
            .order_by(Evaluator.evaluator_id.asc(), Evaluator.version.desc())
        ).all()
    )


def get_evaluator(
    db: Session, project_id: str, evaluator_id: str, version: str
) -> Evaluator | None:
    return db.scalar(
        select(Evaluator).where(
            Evaluator.project_id == project_id,
            Evaluator.evaluator_id == evaluator_id,
            Evaluator.version == version,
        )
    )


def create_suite(
    db: Session,
    *,
    project_id: str,
    suite_id: str,
    version: str,
    name: str,
    definition: dict[str, Any],
    description: str | None = None,
) -> Suite:
    existing = db.scalar(
        select(Suite).where(
            Suite.project_id == project_id,
            Suite.suite_id == suite_id,
            Suite.version == version,
        )
    )
    if existing is not None:
        raise ValueError(f"Suite already exists: {suite_id}@{version}")
    checks = definition.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("suite definition.checks must be a non-empty list")
    for index, check in enumerate(checks):
        if not check.get("evaluator_id") or not check.get("evaluator_version"):
            raise ValueError(
                f"checks[{index}] requires evaluator_id and evaluator_version"
            )
        ev = get_evaluator(
            db, project_id, check["evaluator_id"], check["evaluator_version"]
        )
        if ev is None:
            raise ValueError(
                f"unknown evaluator {check['evaluator_id']}@{check['evaluator_version']}"
            )
    definition = {
        **definition,
        "gate": definition.get("gate") or "all_pass",
    }
    row = Suite(
        project_id=project_id,
        suite_id=suite_id,
        version=version,
        name=name,
        description=description,
        definition=definition,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_suites(db: Session, project_id: str) -> list[Suite]:
    return list(
        db.scalars(
            select(Suite)
            .where(Suite.project_id == project_id)
            .order_by(Suite.suite_id.asc(), Suite.version.desc())
        ).all()
    )


def get_suite(
    db: Session, project_id: str, suite_id: str, version: str | None = None
) -> Suite | None:
    if version:
        return db.scalar(
            select(Suite).where(
                Suite.project_id == project_id,
                Suite.suite_id == suite_id,
                Suite.version == version,
            )
        )
    return db.scalar(
        select(Suite)
        .where(Suite.project_id == project_id, Suite.suite_id == suite_id)
        .order_by(Suite.created_at.desc())
        .limit(1)
    )


def get_eval_job(db: Session, project_id: str, job_id: str) -> EvalJob | None:
    return db.scalar(
        select(EvalJob).where(EvalJob.project_id == project_id, EvalJob.id == job_id)
    )


def list_scores_for_run(db: Session, project_id: str, run_id: str) -> list[Score]:
    return list(
        db.scalars(
            select(Score)
            .where(Score.project_id == project_id, Score.run_id == run_id)
            .order_by(Score.created_at.desc())
        ).all()
    )


def list_scores_for_job(db: Session, job_id: str) -> list[Score]:
    return list(
        db.scalars(select(Score).where(Score.eval_job_id == job_id).order_by(Score.id.asc())).all()
    )


def run_eval_job(
    db: Session,
    *,
    project_id: str,
    run_id: str,
    suite_id: str,
    suite_version: str | None = None,
) -> EvalJob:
    suite = get_suite(db, project_id, suite_id, suite_version)
    if suite is None:
        raise ValueError(f"Suite not found: {suite_id}")

    run = db.scalar(select(Run).where(Run.project_id == project_id, Run.run_id == run_id))
    if run is None:
        raise ValueError(f"Run not found: {run_id}")

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
    metrics_row = db.scalar(
        select(RunMetrics).where(
            RunMetrics.project_id == project_id, RunMetrics.run_id == run_id
        )
    )
    context = run_context(
        run=run.payload,
        spans=[s.payload for s in spans],
        events=[e.payload for e in events],
        metrics=metrics_row.metrics if metrics_row else None,
    )

    job = EvalJob(
        id=f"eval_{uuid4().hex[:16]}",
        project_id=project_id,
        suite_id=suite.suite_id,
        suite_version=suite.version,
        run_id=run_id,
        status="running",
    )
    db.add(job)
    db.flush()

    check_results: list[dict[str, Any]] = []
    try:
        for check in suite.definition.get("checks") or []:
            evaluator = get_evaluator(
                db, project_id, check["evaluator_id"], check["evaluator_version"]
            )
            assert evaluator is not None  # validated at suite create
            raw = _execute_evaluator(evaluator, context)
            passed = apply_threshold(raw, check.get("threshold"))
            score = Score(
                project_id=project_id,
                run_id=run_id,
                eval_job_id=job.id,
                evaluator_id=evaluator.evaluator_id,
                evaluator_version=evaluator.version,
                evaluator_kind=evaluator.kind,
                score_value=raw.get("score_value"),
                passed=passed,
                rationale=raw.get("rationale"),
                details=raw.get("details"),
            )
            db.add(score)
            check_results.append(
                {
                    "evaluator_id": evaluator.evaluator_id,
                    "evaluator_version": evaluator.version,
                    "kind": evaluator.kind,
                    "passed": passed,
                    "score_value": raw.get("score_value"),
                    "rationale": raw.get("rationale"),
                }
            )

        gate = (suite.definition.get("gate") or "all_pass").lower()
        if gate == "all_pass":
            job_passed = all(item["passed"] for item in check_results)
        elif gate == "any_pass":
            job_passed = any(item["passed"] for item in check_results)
        else:
            raise ValueError(f"unsupported suite gate: {gate}")

        job.status = "succeeded"
        job.passed = job_passed
        job.summary = {
            "gate": gate,
            "passed": job_passed,
            "checks": check_results,
            "check_count": len(check_results),
            "pass_count": sum(1 for item in check_results if item["passed"]),
        }
        job.finished_at = utc_now()
        db.commit()
        db.refresh(job)
        return job
    except Exception as exc:  # noqa: BLE001
        job.status = "failed"
        job.passed = False
        job.error_message = str(exc)
        job.finished_at = utc_now()
        job.summary = {"checks": check_results, "error": str(exc)}
        db.commit()
        db.refresh(job)
        return job


def _execute_evaluator(evaluator: Evaluator, context: dict[str, Any]) -> dict[str, Any]:
    if evaluator.kind == "deterministic":
        return evaluate_deterministic(evaluator.config, context)
    if evaluator.kind == "judge":
        return evaluate_judge(evaluator.config, context)
    raise EvaluationError(f"unsupported evaluator kind: {evaluator.kind}")


def _validate_evaluator_config(kind: str, config: dict[str, Any]) -> None:
    # Dry-run against empty context to catch missing keys where possible.
    context = run_context(run={}, spans=[], events=[], metrics={})
    try:
        if kind == "deterministic":
            evaluate_deterministic(config, context)
        elif kind == "judge":
            # stub/heuristic may fail on empty context for contains checks — only validate required keys
            if config.get("mode", "heuristic") == "stub":
                evaluate_judge(config, context)
            else:
                if not config.get("model") or not config.get("prompt_version"):
                    raise EvaluationError("judge config requires 'model' and 'prompt_version'")
                if not config.get("checks"):
                    raise EvaluationError("heuristic judge requires non-empty 'checks'")
        else:
            raise EvaluationError(f"unsupported kind: {kind}")
    except EvaluationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise EvaluationError(str(exc)) from exc


def evaluator_to_dict(row: Evaluator) -> dict[str, Any]:
    return {
        "evaluator_id": row.evaluator_id,
        "version": row.version,
        "kind": row.kind,
        "name": row.name,
        "description": row.description,
        "config": row.config,
        "created_at": row.created_at.isoformat(),
    }


def suite_to_dict(row: Suite) -> dict[str, Any]:
    return {
        "suite_id": row.suite_id,
        "version": row.version,
        "name": row.name,
        "description": row.description,
        "definition": row.definition,
        "created_at": row.created_at.isoformat(),
    }


def job_to_dict(row: EvalJob, scores: list[Score] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": row.id,
        "project_id": row.project_id,
        "suite_id": row.suite_id,
        "suite_version": row.suite_version,
        "run_id": row.run_id,
        "status": row.status,
        "passed": row.passed,
        "summary": row.summary,
        "error_message": row.error_message,
        "created_at": row.created_at.isoformat(),
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
    }
    if scores is not None:
        payload["scores"] = [score_to_dict(s) for s in scores]
    return payload


def score_to_dict(row: Score) -> dict[str, Any]:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "run_id": row.run_id,
        "eval_job_id": row.eval_job_id,
        "evaluator_id": row.evaluator_id,
        "evaluator_version": row.evaluator_version,
        "evaluator_kind": row.evaluator_kind,
        "score_value": row.score_value,
        "passed": row.passed,
        "rationale": row.rationale,
        "details": row.details,
        "created_at": row.created_at.isoformat(),
    }
