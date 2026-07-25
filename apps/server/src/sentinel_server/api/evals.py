"""Evaluation registry and job APIs."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from sentinel_server.auth import require_auth
from sentinel_server.db import get_db
from sentinel_server.services import evaluation as evalsvc
from sentinel_server.services import queries
from sentinel_server.services.eval_engine import EvaluationError

router = APIRouter(prefix="/v1", tags=["evals"])


class EvaluatorCreate(BaseModel):
    evaluator_id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    kind: Literal["deterministic", "judge"]
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    config: dict[str, Any]


class SuiteCreate(BaseModel):
    suite_id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    definition: dict[str, Any]


class EvalJobCreate(BaseModel):
    run_id: str = Field(min_length=1, max_length=128)
    suite_id: str = Field(min_length=1, max_length=128)
    suite_version: str | None = Field(default=None, max_length=64)


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


@router.post("/projects/{project_id}/evaluators", status_code=status.HTTP_201_CREATED)
def create_evaluator(
    project_id: str,
    body: EvaluatorCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    try:
        row = evalsvc.create_evaluator(
            db,
            project_id=project_id,
            evaluator_id=body.evaluator_id,
            version=body.version,
            kind=body.kind,
            name=body.name,
            description=body.description,
            config=body.config,
        )
    except (ValueError, EvaluationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "EVALUATOR_INVALID", "message": str(exc)}},
        ) from exc
    return evalsvc.evaluator_to_dict(row)


@router.get("/projects/{project_id}/evaluators")
def list_evaluators(
    project_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    items = evalsvc.list_evaluators(db, project_id)
    return {"items": [evalsvc.evaluator_to_dict(item) for item in items]}


@router.get("/projects/{project_id}/evaluators/{evaluator_id}")
def get_evaluator_versions(
    project_id: str,
    evaluator_id: str,
    version: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    if version:
        row = evalsvc.get_evaluator(db, project_id, evaluator_id, version)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Evaluator not found: {evaluator_id}@{version}",
                    }
                },
            )
        return evalsvc.evaluator_to_dict(row)
    items = [
        item
        for item in evalsvc.list_evaluators(db, project_id)
        if item.evaluator_id == evaluator_id
    ]
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Evaluator not found: {evaluator_id}",
                }
            },
        )
    return {"items": [evalsvc.evaluator_to_dict(item) for item in items]}


@router.post("/projects/{project_id}/suites", status_code=status.HTTP_201_CREATED)
def create_suite(
    project_id: str,
    body: SuiteCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    try:
        row = evalsvc.create_suite(
            db,
            project_id=project_id,
            suite_id=body.suite_id,
            version=body.version,
            name=body.name,
            description=body.description,
            definition=body.definition,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "SUITE_INVALID", "message": str(exc)}},
        ) from exc
    return evalsvc.suite_to_dict(row)


@router.get("/projects/{project_id}/suites")
def list_suites(
    project_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    items = evalsvc.list_suites(db, project_id)
    return {"items": [evalsvc.suite_to_dict(item) for item in items]}


@router.get("/projects/{project_id}/suites/{suite_id}")
def get_suite(
    project_id: str,
    suite_id: str,
    version: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    row = evalsvc.get_suite(db, project_id, suite_id, version)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Suite not found: {suite_id}",
                }
            },
        )
    return evalsvc.suite_to_dict(row)


@router.post("/projects/{project_id}/evals", status_code=status.HTTP_202_ACCEPTED)
def create_eval_job(
    project_id: str,
    body: EvalJobCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    """Run a suite against a run. Executes synchronously; returns completed job."""
    _require_project(db, project_id)
    try:
        job = evalsvc.run_eval_job(
            db,
            project_id=project_id,
            run_id=body.run_id,
            suite_id=body.suite_id,
            suite_version=body.suite_version,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "EVAL_INVALID", "message": str(exc)}},
        ) from exc
    scores = evalsvc.list_scores_for_job(db, job.id)
    return evalsvc.job_to_dict(job, scores=scores)


@router.get("/projects/{project_id}/evals/{job_id}")
def get_eval_job(
    project_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    job = evalsvc.get_eval_job(db, project_id, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Eval job not found: {job_id}",
                }
            },
        )
    scores = evalsvc.list_scores_for_job(db, job.id)
    return evalsvc.job_to_dict(job, scores=scores)


@router.get("/projects/{project_id}/runs/{run_id}/scores")
def list_run_scores(
    project_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    if queries.get_run_detail(db, project_id, run_id, include_spans=False, include_events=False, include_metrics=False) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Run not found: {run_id}",
                }
            },
        )
    scores = evalsvc.list_scores_for_run(db, project_id, run_id)
    return {"items": [evalsvc.score_to_dict(item) for item in scores]}
