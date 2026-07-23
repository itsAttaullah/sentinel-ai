"""API auth dependency."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from sentinel_server.config import get_settings


def require_auth(x_sentinel_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if settings.auth_mode == "local":
        return
    if not x_sentinel_api_key or x_sentinel_api_key not in settings.api_key_set:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Valid X-Sentinel-Api-Key header required",
                }
            },
        )
