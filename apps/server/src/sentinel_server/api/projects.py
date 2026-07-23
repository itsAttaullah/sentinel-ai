"""Project and run routes."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from sentinel_server.auth import require_auth
from sentinel_server.db import get_db
from sentinel_server.services import queries

router = APIRouter(prefix="/v1", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    id: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None


class ProjectOut(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_at: datetime


@router.get("/projects")
def list_projects(
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, list[dict[str, Any]]]:
    items = queries.list_projects(db)
    return {
        "items": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "created_at": p.created_at.isoformat(),
            }
            for p in items
        ]
    }


@router.post("/projects", status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    try:
        project = queries.create_project(
            db, name=body.name, project_id=body.id, description=body.description
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "PROJECT_EXISTS",
                    "message": str(exc),
                }
            },
        ) from exc
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
    }


@router.get("/projects/{project_id}")
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    project = queries.get_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Project not found: {project_id}",
                }
            },
        )
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
    }


@router.get("/projects/{project_id}/runs")
def list_runs(
    project_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    agent_version: str | None = None,
    tag: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
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
    runs = queries.list_runs(
        db,
        project_id,
        status=status_filter,
        agent_version=agent_version,
        tag=tag,
        limit=limit,
    )
    return {
        "items": [
            {
                "run_id": run.run_id,
                "name": run.name,
                "agent_name": run.agent_name,
                "agent_version": run.agent_version,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "ended_at": run.ended_at.isoformat() if run.ended_at else None,
                "tags": run.tags,
            }
            for run in runs
        ]
    }


@router.get("/projects/{project_id}/runs/{run_id}")
def get_run(
    project_id: str,
    run_id: str,
    include: str = Query(default="spans,events"),
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    parts = {part.strip() for part in include.split(",") if part.strip()}
    detail = queries.get_run_detail(
        db,
        project_id,
        run_id,
        include_spans="spans" in parts,
        include_events="events" in parts,
    )
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Run not found: {run_id}",
                }
            },
        )
    return detail


@router.get("/quarantine")
def get_quarantine(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    items = queries.list_quarantine(db, limit=limit)
    return {
        "items": [
            {
                "id": item.id,
                "project_id": item.project_id,
                "error_code": item.error_code,
                "message": item.message,
                "details": item.details,
                "created_at": item.created_at.isoformat(),
            }
            for item in items
        ]
    }
