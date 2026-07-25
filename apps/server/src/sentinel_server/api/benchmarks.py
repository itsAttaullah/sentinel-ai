"""Benchmark suite, cell, and comparison APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from sentinel_server.auth import require_auth
from sentinel_server.db import get_db
from sentinel_server.services import benchmarking as benchsvc
from sentinel_server.services import queries

router = APIRouter(prefix="/v1", tags=["benchmarks"])


class BenchmarkSuiteCreate(BaseModel):
    benchmark_id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    definition: dict[str, Any]


class BenchmarkCellCreate(BaseModel):
    task_id: str = Field(min_length=1, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    dimensions: dict[str, Any] | None = None
    environment: dict[str, Any] | None = None
    cell_id: str | None = Field(default=None, max_length=128)
    eval_job_id: str | None = Field(default=None, max_length=64)
    run_eval: bool = False
    benchmark_version: str | None = Field(default=None, max_length=64)


class BenchmarkJobCreate(BaseModel):
    """OpenAPI-compatible create body; suite_id aliases benchmark_id."""

    suite_id: str | None = Field(default=None, max_length=128)
    benchmark_id: str | None = Field(default=None, max_length=128)
    benchmark_version: str | None = Field(default=None, max_length=64)
    baseline_agent_version: str | None = Field(default=None, max_length=128)

    def resolved_benchmark_id(self) -> str:
        value = self.benchmark_id or self.suite_id
        if not value:
            raise ValueError("benchmark_id or suite_id is required")
        return value


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
    "/projects/{project_id}/benchmark-suites",
    status_code=status.HTTP_201_CREATED,
)
def create_benchmark_suite(
    project_id: str,
    body: BenchmarkSuiteCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    try:
        row = benchsvc.create_benchmark_suite(
            db,
            project_id=project_id,
            benchmark_id=body.benchmark_id,
            version=body.version,
            name=body.name,
            description=body.description,
            definition=body.definition,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "BENCHMARK_INVALID", "message": str(exc)}},
        ) from exc
    return benchsvc.suite_to_dict(row)


@router.get("/projects/{project_id}/benchmark-suites")
def list_benchmark_suites(
    project_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    items = benchsvc.list_benchmark_suites(db, project_id)
    return {"items": [benchsvc.suite_to_dict(item) for item in items]}


@router.get("/projects/{project_id}/benchmark-suites/{benchmark_id}")
def get_benchmark_suite(
    project_id: str,
    benchmark_id: str,
    version: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    row = benchsvc.get_benchmark_suite(db, project_id, benchmark_id, version)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Benchmark suite not found: {benchmark_id}",
                }
            },
        )
    return benchsvc.suite_to_dict(row)


@router.post(
    "/projects/{project_id}/benchmark-suites/{benchmark_id}/cells",
    status_code=status.HTTP_201_CREATED,
)
def register_benchmark_cell(
    project_id: str,
    benchmark_id: str,
    body: BenchmarkCellCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    try:
        row = benchsvc.register_cell(
            db,
            project_id=project_id,
            benchmark_id=benchmark_id,
            benchmark_version=body.benchmark_version,
            task_id=body.task_id,
            run_id=body.run_id,
            dimensions=body.dimensions,
            environment=body.environment,
            cell_id=body.cell_id,
            eval_job_id=body.eval_job_id,
            run_eval=body.run_eval,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "BENCHMARK_CELL_INVALID", "message": str(exc)}},
        ) from exc
    return benchsvc.cell_to_dict(row)


@router.get("/projects/{project_id}/benchmark-suites/{benchmark_id}/cells")
def list_benchmark_cells(
    project_id: str,
    benchmark_id: str,
    version: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    suite = benchsvc.get_benchmark_suite(db, project_id, benchmark_id, version)
    if suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Benchmark suite not found: {benchmark_id}",
                }
            },
        )
    items = benchsvc.list_cells(db, project_id, suite.benchmark_id, suite.version)
    return {"items": [benchsvc.cell_to_dict(item) for item in items]}


@router.get("/projects/{project_id}/benchmark-suites/{benchmark_id}/leaderboard")
def get_leaderboard(
    project_id: str,
    benchmark_id: str,
    version: str | None = Query(default=None),
    baseline_agent_version: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    suite = benchsvc.get_benchmark_suite(db, project_id, benchmark_id, version)
    if suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Benchmark suite not found: {benchmark_id}",
                }
            },
        )
    cells = benchsvc.list_cells(db, project_id, suite.benchmark_id, suite.version)
    report = benchsvc.build_leaderboard(
        cells, baseline_agent_version=baseline_agent_version
    )
    report["benchmark_id"] = suite.benchmark_id
    report["benchmark_version"] = suite.version
    report["name"] = suite.name
    return report


@router.post("/projects/{project_id}/benchmarks", status_code=status.HTTP_202_ACCEPTED)
def create_benchmark_job(
    project_id: str,
    body: BenchmarkJobCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    """Build a comparison report over registered cells (sync)."""
    _require_project(db, project_id)
    try:
        benchmark_id = body.resolved_benchmark_id()
        job = benchsvc.run_benchmark_job(
            db,
            project_id=project_id,
            benchmark_id=benchmark_id,
            benchmark_version=body.benchmark_version,
            baseline_agent_version=body.baseline_agent_version,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "BENCHMARK_INVALID", "message": str(exc)}},
        ) from exc
    return benchsvc.job_to_dict(job)


@router.get("/projects/{project_id}/benchmarks/{job_id}")
def get_benchmark_job(
    project_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    _require_project(db, project_id)
    job = benchsvc.get_benchmark_job(db, project_id, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Benchmark job not found: {job_id}",
                }
            },
        )
    return benchsvc.job_to_dict(job)
