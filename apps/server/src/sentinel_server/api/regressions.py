"""Regression policies, baselines, compare/gate APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from sentinel_server.auth import require_auth
from sentinel_server.db import get_db
from sentinel_server.services import queries
from sentinel_server.services import regression as regsvc

router = APIRouter(prefix="/v1", tags=["regressions"])


class PolicyCreate(BaseModel):
    policy_id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    definition: dict[str, Any] | None = None


class BaselineCreate(BaseModel):
    baseline_id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    reference: dict[str, Any]


class RegressionRequest(BaseModel):
    baseline: dict[str, Any]
    candidate: dict[str, Any]
    policy_id: str | None = Field(default=None, max_length=128)
    policy_version: str | None = Field(default=None, max_length=64)
    policy_definition: dict[str, Any] | None = None


def _require_project(db: Session, project_id: str) -> None:
    if queries.get_project(db, project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Project not found: {project_id}",
                }
            },
        )


@router.post(
    "/projects/{project_id}/regression-policies",
    status_code=status.HTTP_201_CREATED,
)
def create_policy(
    project_id: str,
    body: PolicyCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    try:
        row = regsvc.create_policy(
            db,
            project_id=project_id,
            policy_id=body.policy_id,
            version=body.version,
            name=body.name,
            description=body.description,
            definition=body.definition,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "POLICY_INVALID", "message": str(exc)}},
        ) from exc
    return regsvc.policy_to_dict(row)


@router.get("/projects/{project_id}/regression-policies")
def list_policies(
    project_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    items = regsvc.list_policies(db, project_id)
    return {"items": [regsvc.policy_to_dict(item) for item in items]}


@router.get("/projects/{project_id}/regression-policies/{policy_id}")
def get_policy(
    project_id: str,
    policy_id: str,
    version: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    row = regsvc.get_policy(db, project_id, policy_id, version)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Policy not found: {policy_id}",
                }
            },
        )
    return regsvc.policy_to_dict(row)


@router.post(
    "/projects/{project_id}/baselines",
    status_code=status.HTTP_201_CREATED,
)
def create_baseline(
    project_id: str,
    body: BaselineCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    try:
        row = regsvc.create_baseline(
            db,
            project_id=project_id,
            baseline_id=body.baseline_id,
            version=body.version,
            name=body.name,
            description=body.description,
            reference=body.reference,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "BASELINE_INVALID", "message": str(exc)}},
        ) from exc
    return regsvc.baseline_to_dict(row)


@router.get("/projects/{project_id}/baselines")
def list_baselines(
    project_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    items = regsvc.list_baselines(db, project_id)
    return {"items": [regsvc.baseline_to_dict(item) for item in items]}


@router.post(
    "/projects/{project_id}/regressions/compare",
    status_code=status.HTTP_202_ACCEPTED,
)
def compare_versions(
    project_id: str,
    body: RegressionRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    """Diff baseline vs candidate metrics/scores (no pass/fail)."""
    _require_project(db, project_id)
    job = regsvc.run_compare_or_gate(
        db,
        project_id=project_id,
        kind="compare",
        baseline_ref=body.baseline,
        candidate_ref=body.candidate,
    )
    return regsvc.job_to_dict(job)


@router.post(
    "/projects/{project_id}/regressions/gate",
    status_code=status.HTTP_202_ACCEPTED,
)
def gate_versions(
    project_id: str,
    body: RegressionRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    """
    Apply a threshold policy and return pass/fail.

    HTTP status stays 202 even when the gate fails; use ``passed`` /
    ``exit_code_hint`` for CI (0 pass, 1 fail, 2 error).
    """
    _require_project(db, project_id)
    job = regsvc.run_compare_or_gate(
        db,
        project_id=project_id,
        kind="gate",
        baseline_ref=body.baseline,
        candidate_ref=body.candidate,
        policy_id=body.policy_id,
        policy_version=body.policy_version,
        policy_definition=body.policy_definition,
    )
    return regsvc.job_to_dict(job)


@router.get("/projects/{project_id}/regressions/{job_id}")
def get_regression_job(
    project_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    job = regsvc.get_regression_job(db, project_id, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Regression job not found: {job_id}",
                }
            },
        )
    return regsvc.job_to_dict(job)
