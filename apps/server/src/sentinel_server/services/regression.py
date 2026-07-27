"""Regression policies, baseline pins, compare/gate jobs."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from sentinel_server.models import (
    BaselinePin,
    EvalJob,
    RegressionJob,
    RegressionPolicy,
    Run,
    RunMetrics,
    Score,
    utc_now,
)
from sentinel_server.services.regression_engine import apply_policy, default_ci_policy


def create_policy(
    db: Session,
    *,
    project_id: str,
    policy_id: str,
    version: str,
    name: str,
    definition: dict[str, Any] | None = None,
    description: str | None = None,
) -> RegressionPolicy:
    existing = db.scalar(
        select(RegressionPolicy).where(
            RegressionPolicy.project_id == project_id,
            RegressionPolicy.policy_id == policy_id,
            RegressionPolicy.version == version,
        )
    )
    if existing is not None:
        raise ValueError(f"Policy already exists: {policy_id}@{version}")
    row = RegressionPolicy(
        project_id=project_id,
        policy_id=policy_id,
        version=version,
        name=name,
        description=description,
        definition=definition or default_ci_policy(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_policies(db: Session, project_id: str) -> list[RegressionPolicy]:
    return list(
        db.scalars(
            select(RegressionPolicy)
            .where(RegressionPolicy.project_id == project_id)
            .order_by(RegressionPolicy.policy_id.asc(), RegressionPolicy.version.desc())
        ).all()
    )


def get_policy(
    db: Session, project_id: str, policy_id: str, version: str | None = None
) -> RegressionPolicy | None:
    if version:
        return db.scalar(
            select(RegressionPolicy).where(
                RegressionPolicy.project_id == project_id,
                RegressionPolicy.policy_id == policy_id,
                RegressionPolicy.version == version,
            )
        )
    return db.scalar(
        select(RegressionPolicy)
        .where(
            RegressionPolicy.project_id == project_id,
            RegressionPolicy.policy_id == policy_id,
        )
        .order_by(RegressionPolicy.created_at.desc())
        .limit(1)
    )


def create_baseline(
    db: Session,
    *,
    project_id: str,
    baseline_id: str,
    version: str,
    name: str,
    reference: dict[str, Any],
    description: str | None = None,
) -> BaselinePin:
    kind = reference.get("kind")
    if kind not in {"agent_version", "run_ids"}:
        raise ValueError("baseline reference.kind must be 'agent_version' or 'run_ids'")
    if kind == "agent_version" and not reference.get("agent_version"):
        raise ValueError("agent_version baseline requires reference.agent_version")
    if kind == "run_ids":
        run_ids = reference.get("run_ids")
        if not isinstance(run_ids, list) or not run_ids:
            raise ValueError("run_ids baseline requires non-empty reference.run_ids")
    existing = db.scalar(
        select(BaselinePin).where(
            BaselinePin.project_id == project_id,
            BaselinePin.baseline_id == baseline_id,
            BaselinePin.version == version,
        )
    )
    if existing is not None:
        raise ValueError(f"Baseline already exists: {baseline_id}@{version}")
    row = BaselinePin(
        project_id=project_id,
        baseline_id=baseline_id,
        version=version,
        name=name,
        description=description,
        reference=reference,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_baselines(db: Session, project_id: str) -> list[BaselinePin]:
    return list(
        db.scalars(
            select(BaselinePin)
            .where(BaselinePin.project_id == project_id)
            .order_by(BaselinePin.baseline_id.asc(), BaselinePin.version.desc())
        ).all()
    )


def get_baseline(
    db: Session, project_id: str, baseline_id: str, version: str | None = None
) -> BaselinePin | None:
    if version:
        return db.scalar(
            select(BaselinePin).where(
                BaselinePin.project_id == project_id,
                BaselinePin.baseline_id == baseline_id,
                BaselinePin.version == version,
            )
        )
    return db.scalar(
        select(BaselinePin)
        .where(
            BaselinePin.project_id == project_id,
            BaselinePin.baseline_id == baseline_id,
        )
        .order_by(BaselinePin.created_at.desc())
        .limit(1)
    )


def resolve_ref(db: Session, project_id: str, ref: dict[str, Any]) -> dict[str, Any]:
    """Resolve a compare/gate ref into a metrics+scores snapshot."""
    kind = ref.get("kind")
    if kind == "baseline":
        pin = get_baseline(
            db, project_id, str(ref["baseline_id"]), ref.get("baseline_version")
        )
        if pin is None:
            raise ValueError(f"Baseline not found: {ref.get('baseline_id')}")
        return resolve_ref(db, project_id, pin.reference)

    if kind == "agent_version":
        version = str(ref.get("agent_version") or "")
        if not version:
            raise ValueError("agent_version ref requires agent_version")
        runs = list(
            db.scalars(
                select(Run).where(
                    Run.project_id == project_id, Run.agent_version == version
                )
            ).all()
        )
        if not runs:
            raise ValueError(f"No runs for agent_version={version}")
        return _aggregate_runs(db, project_id, runs, label={"kind": kind, "agent_version": version})

    if kind == "run_ids":
        run_ids = list(ref.get("run_ids") or [])
        if not run_ids:
            raise ValueError("run_ids ref requires run_ids")
        runs = []
        for run_id in run_ids:
            row = db.scalar(
                select(Run).where(Run.project_id == project_id, Run.run_id == run_id)
            )
            if row is None:
                raise ValueError(f"Run not found: {run_id}")
            runs.append(row)
        return _aggregate_runs(
            db, project_id, runs, label={"kind": kind, "run_ids": run_ids}
        )

    if kind == "run":
        run_id = str(ref.get("run_id") or "")
        if not run_id:
            raise ValueError("run ref requires run_id")
        return resolve_ref(db, project_id, {"kind": "run_ids", "run_ids": [run_id]})

    raise ValueError(
        "ref.kind must be one of: baseline, agent_version, run_ids, run"
    )


def run_compare_or_gate(
    db: Session,
    *,
    project_id: str,
    kind: str,
    baseline_ref: dict[str, Any],
    candidate_ref: dict[str, Any],
    policy_id: str | None = None,
    policy_version: str | None = None,
    policy_definition: dict[str, Any] | None = None,
) -> RegressionJob:
    if kind not in {"compare", "gate"}:
        raise ValueError("kind must be 'compare' or 'gate'")

    policy_row = None
    definition = policy_definition
    if kind == "gate":
        if definition is None:
            if not policy_id:
                # use ephemeral default
                definition = default_ci_policy()
                policy_id = "default"
                policy_version = policy_version or "builtin"
            else:
                policy_row = get_policy(db, project_id, policy_id, policy_version)
                if policy_row is None:
                    raise ValueError(f"Policy not found: {policy_id}")
                definition = policy_row.definition
                policy_version = policy_row.version
        elif policy_id is None:
            policy_id = "inline"
            policy_version = policy_version or "inline"

    job = RegressionJob(
        id=f"reg_{uuid4().hex[:16]}",
        project_id=project_id,
        kind=kind,
        policy_id=policy_id,
        policy_version=policy_version if kind == "gate" else None,
        baseline_ref=baseline_ref,
        candidate_ref=candidate_ref,
        status="running",
    )
    db.add(job)
    db.flush()

    try:
        baseline = resolve_ref(db, project_id, baseline_ref)
        candidate = resolve_ref(db, project_id, candidate_ref)
        diff = {
            "metrics_delta": _delta_maps(
                baseline.get("metrics") or {}, candidate.get("metrics") or {}
            ),
            "scores_delta": _delta_maps(
                baseline.get("scores") or {}, candidate.get("scores") or {}
            ),
        }
        report: dict[str, Any] = {
            "kind": kind,
            "baseline": baseline,
            "candidate": candidate,
            "diff": diff,
        }
        if kind == "gate":
            assert definition is not None
            gate = apply_policy(
                baseline=baseline, candidate=candidate, policy=definition
            )
            report["gate"] = gate
            report["policy"] = {
                "policy_id": policy_id,
                "policy_version": policy_version,
                "definition": definition,
            }
            job.passed = bool(gate["passed"])
        else:
            job.passed = None

        job.report = report
        job.status = "succeeded"
        job.finished_at = utc_now()
        db.commit()
        db.refresh(job)
        return job
    except Exception as exc:  # noqa: BLE001
        job.status = "failed"
        job.passed = False if kind == "gate" else None
        job.error_message = str(exc)
        job.finished_at = utc_now()
        db.commit()
        db.refresh(job)
        return job


def get_regression_job(
    db: Session, project_id: str, job_id: str
) -> RegressionJob | None:
    return db.scalar(
        select(RegressionJob).where(
            RegressionJob.project_id == project_id, RegressionJob.id == job_id
        )
    )


def policy_to_dict(row: RegressionPolicy) -> dict[str, Any]:
    return {
        "policy_id": row.policy_id,
        "version": row.version,
        "name": row.name,
        "description": row.description,
        "definition": row.definition,
        "created_at": row.created_at.isoformat(),
    }


def baseline_to_dict(row: BaselinePin) -> dict[str, Any]:
    return {
        "baseline_id": row.baseline_id,
        "version": row.version,
        "name": row.name,
        "description": row.description,
        "reference": row.reference,
        "created_at": row.created_at.isoformat(),
    }


def job_to_dict(row: RegressionJob) -> dict[str, Any]:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "kind": row.kind,
        "policy_id": row.policy_id,
        "policy_version": row.policy_version,
        "baseline_ref": row.baseline_ref,
        "candidate_ref": row.candidate_ref,
        "status": row.status,
        "passed": row.passed,
        "report": row.report,
        "error_message": row.error_message,
        "created_at": row.created_at.isoformat(),
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        "exit_code_hint": _exit_code_hint(row),
    }


def _exit_code_hint(row: RegressionJob) -> int:
    if row.status == "failed":
        return 2
    if row.kind == "gate" and row.passed is False:
        return 1
    return 0


def _aggregate_runs(
    db: Session, project_id: str, runs: list[Run], *, label: dict[str, Any]
) -> dict[str, Any]:
    walls: list[float] = []
    costs: list[float] = []
    retries: list[float] = []
    tokens_in: list[float] = []
    tokens_out: list[float] = []
    success = 0
    pass_rates: list[float] = []
    mean_scores: list[float] = []
    eval_passed_flags: list[bool] = []

    for run in runs:
        if run.status == "succeeded":
            success += 1
        metrics = db.scalar(
            select(RunMetrics).where(
                RunMetrics.project_id == project_id, RunMetrics.run_id == run.run_id
            )
        )
        if metrics:
            if metrics.wall_ms is not None:
                walls.append(float(metrics.wall_ms))
            if metrics.estimated_cost_usd is not None:
                costs.append(float(metrics.estimated_cost_usd))
            retries.append(float(metrics.retry_count or 0))
            tokens_in.append(float(metrics.tokens_in or 0))
            tokens_out.append(float(metrics.tokens_out or 0))

        # latest succeeded eval job for the run
        job = db.scalar(
            select(EvalJob)
            .where(
                EvalJob.project_id == project_id,
                EvalJob.run_id == run.run_id,
                EvalJob.status == "succeeded",
            )
            .order_by(EvalJob.created_at.desc())
            .limit(1)
        )
        if job is not None:
            if job.passed is not None:
                eval_passed_flags.append(bool(job.passed))
            scores = list(
                db.scalars(select(Score).where(Score.eval_job_id == job.id)).all()
            )
            if scores:
                vals = [s.score_value for s in scores if s.score_value is not None]
                if vals:
                    mean_scores.append(sum(float(v) for v in vals) / len(vals))
                pass_rates.append(
                    sum(1 for s in scores if s.passed) / len(scores)
                )

    count = len(runs)
    snapshot = {
        "label": label,
        "run_count": count,
        "run_ids": [r.run_id for r in runs],
        "metrics": {
            "wall_ms": _mean(walls),
            "estimated_cost_usd": _mean(costs),
            "retry_count": _mean(retries),
            "tokens_in": _mean(tokens_in),
            "tokens_out": _mean(tokens_out),
            "success_rate": (success / count) if count else None,
        },
        "scores": {
            "pass_rate": _mean(pass_rates),
            "mean_score": _mean(mean_scores),
            "passed": all(eval_passed_flags) if eval_passed_flags else None,
            "eval_job_count": len(eval_passed_flags),
        },
    }
    return snapshot


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _delta_maps(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    keys = set(a) | set(b)
    out: dict[str, Any] = {}
    for key in sorted(keys):
        av = a.get(key)
        bv = b.get(key)
        if isinstance(av, (int, float)) and isinstance(bv, (int, float)):
            out[key] = round(float(bv) - float(av), 6)
        else:
            out[key] = {"baseline": av, "candidate": bv}
    return out
