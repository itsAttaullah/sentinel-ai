"""Health endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from sentinel_server import __version__
from sentinel_server.db import db_ready

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "version": __version__}


@router.get("/readyz")
def readyz() -> JSONResponse:
    if db_ready():
        return JSONResponse({"status": "ok", "version": __version__})
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "code": "NOT_READY",
                "message": "Database is not reachable",
            }
        },
    )
