"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from sentinel_server import __version__
from sentinel_server.api import health, ingest, projects
from sentinel_server.db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Sentinel AI API",
    version=__version__,
    description="Ingest gateway and control plane for Sentinel AI traces.",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(projects.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "REQUEST_VALIDATION_FAILED",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            }
        },
    )


def create_app(*, database_url: str | None = None) -> FastAPI:
    """Factory used by tests to bind a temporary database."""

    @asynccontextmanager
    async def _lifespan(_app: FastAPI):
        init_db(database_url)
        yield

    test_app = FastAPI(
        title="Sentinel AI API",
        version=__version__,
        lifespan=_lifespan,
    )
    test_app.include_router(health.router)
    test_app.include_router(ingest.router)
    test_app.include_router(projects.router)
    test_app.add_exception_handler(RequestValidationError, validation_exception_handler)
    return test_app
