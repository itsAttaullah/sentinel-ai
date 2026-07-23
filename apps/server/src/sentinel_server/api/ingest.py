"""Ingest endpoint."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from sentinel_server.auth import require_auth
from sentinel_server.config import get_settings
from sentinel_server.db import get_db
from sentinel_server.services.ingest import persist_ingest_batch, quarantine
from sentinel_server.validation import (
    SchemaValidationError,
    assert_project_consistency,
    validate_ingest_batch,
)

router = APIRouter(prefix="/v1", tags=["ingest"])


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def post_ingest(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    settings = get_settings()
    body = await request.body()
    if len(body) > settings.max_body_bytes:
        quarantine(
            db,
            error_code="PAYLOAD_TOO_LARGE",
            message=f"Body exceeds {settings.max_body_bytes} bytes",
            payload={"size": len(body)},
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": {
                    "code": "PAYLOAD_TOO_LARGE",
                    "message": f"Body exceeds {settings.max_body_bytes} bytes",
                }
            },
        )

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        quarantine(
            db,
            error_code="INVALID_JSON",
            message="Request body is not valid JSON",
            payload={"raw_size": len(body)},
            details={"exception": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_JSON",
                    "message": "Request body is not valid JSON",
                }
            },
        ) from exc

    project_id = payload.get("project_id") if isinstance(payload, dict) else None
    try:
        validate_ingest_batch(payload)
        assert isinstance(payload, dict)
        assert_project_consistency(payload)
    except SchemaValidationError as exc:
        quarantine(
            db,
            error_code="SCHEMA_VALIDATION_FAILED",
            message=exc.message,
            payload=payload if isinstance(payload, (dict, list)) else None,
            details=exc.errors,
            project_id=project_id if isinstance(project_id, str) else None,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "SCHEMA_VALIDATION_FAILED",
                    "message": exc.message,
                    "details": {"errors": exc.errors},
                }
            },
        ) from exc

    counts = persist_ingest_batch(db, payload)
    return {
        "accepted": True,
        "project_id": payload["project_id"],
        "batch_id": payload.get("batch_id"),
        "counts": counts,
    }
