"""API auth with optional key scopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import Header, HTTPException, status

from sentinel_server.config import get_settings

# Scope grants (a key may list several, pipe-separated in config)
SCOPE_ADMIN = "admin"
SCOPE_INGEST = "ingest"
SCOPE_READ = "read"
SCOPE_WRITE = "write"

READ_OK = frozenset({SCOPE_READ, SCOPE_WRITE, SCOPE_ADMIN, SCOPE_INGEST})
INGEST_OK = frozenset({SCOPE_INGEST, SCOPE_WRITE, SCOPE_ADMIN})
WRITE_OK = frozenset({SCOPE_WRITE, SCOPE_ADMIN})


@dataclass(frozen=True, slots=True)
class AuthContext:
    mode: str
    key: str | None
    scopes: frozenset[str]


def _parse_scope_map(raw: str) -> dict[str, frozenset[str]]:
    """
    Parse SENTINEL_API_KEY_SCOPES.

    Format: ``key1:admin,key2:ingest|read,key3:write``
    Keys omitted from the map default to ``admin`` (backward compatible).
    """
    mapping: dict[str, frozenset[str]] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            continue
        key, scopes_raw = part.split(":", 1)
        key = key.strip()
        scopes = {s.strip() for s in scopes_raw.split("|") if s.strip()}
        if key and scopes:
            mapping[key] = frozenset(scopes)
    return mapping


def _unauthorized(message: str = "Valid X-Sentinel-Api-Key header required") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": "UNAUTHORIZED", "message": message}},
    )


def _forbidden(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"error": {"code": "FORBIDDEN", "message": message}},
    )


def resolve_auth(x_sentinel_api_key: str | None) -> AuthContext:
    settings = get_settings()
    if settings.auth_mode == "local":
        return AuthContext(mode="local", key=None, scopes=frozenset({SCOPE_ADMIN}))

    if not x_sentinel_api_key or x_sentinel_api_key not in settings.api_key_set:
        raise _unauthorized()

    scope_map = _parse_scope_map(settings.api_key_scopes)
    scopes = scope_map.get(x_sentinel_api_key, frozenset({SCOPE_ADMIN}))
    return AuthContext(mode="api_key", key=x_sentinel_api_key, scopes=scopes)


def _make_dependency(allowed: frozenset[str] | None) -> Callable[..., AuthContext]:
    def dependency(
        x_sentinel_api_key: str | None = Header(default=None),
    ) -> AuthContext:
        ctx = resolve_auth(x_sentinel_api_key)
        if allowed is None:
            return ctx
        if ctx.scopes & allowed:
            return ctx
        raise _forbidden(
            f"API key missing required scope; need one of: {', '.join(sorted(allowed))}"
        )

    return dependency


# Any authenticated principal (local mode or valid key)
require_auth = _make_dependency(None)
require_read = _make_dependency(READ_OK)
require_ingest = _make_dependency(INGEST_OK)
require_write = _make_dependency(WRITE_OK)
