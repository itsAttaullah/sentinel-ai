"""Application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_schema_dir() -> Path:
    """Resolve monorepo schema dir when running from source or Compose."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[4] / "packages" / "schema" / "jsonschema" / "v1",  # .../apps/server/src/sentinel_server
        here.parents[3] / "packages" / "schema" / "jsonschema" / "v1",
        Path("/schema/jsonschema/v1"),
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[0]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SENTINEL_",
        env_file=".env",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+psycopg://sentinel:sentinel@localhost:5432/sentinel"
    )
    schema_dir: Path = Field(default_factory=_default_schema_dir)
    pricing_path: Path | None = None
    auth_mode: Literal["local", "api_key"] = "local"
    api_keys: str = ""
    max_body_bytes: int = 10 * 1024 * 1024
    app_version: str = "0.3.0"

    @property
    def api_key_set(self) -> set[str]:
        return {part.strip() for part in self.api_keys.split(",") if part.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
