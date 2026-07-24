"""CLI configuration loading and persistence."""

from __future__ import annotations

import os
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_API_URL = "http://localhost:8080"
DEFAULT_PROJECT_ID = "proj_demo"


@dataclass
class CliConfig:
    api_url: str = DEFAULT_API_URL
    project_id: str = DEFAULT_PROJECT_ID
    api_key: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "api_url": self.api_url,
            "project_id": self.project_id,
            "api_key_set": bool(self.api_key),
        }


def project_config_path(cwd: Path | None = None) -> Path:
    base = cwd or Path.cwd()
    return base / ".sentinel" / "config.toml"


def load_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def write_config(path: Path, config: CliConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f'api_url = "{config.api_url}"',
        f'project_id = "{config.project_id}"',
    ]
    if config.api_key:
        lines.append(f'api_key = "{config.api_key}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_config(
    *,
    api_url: str | None = None,
    project_id: str | None = None,
    api_key: str | None = None,
    cwd: Path | None = None,
) -> CliConfig:
    file_cfg = load_toml(project_config_path(cwd))
    return CliConfig(
        api_url=(
            api_url
            or os.environ.get("SENTINEL_API_URL")
            or str(file_cfg.get("api_url") or DEFAULT_API_URL)
        ).rstrip("/"),
        project_id=(
            project_id
            or os.environ.get("SENTINEL_PROJECT_ID")
            or str(file_cfg.get("project_id") or DEFAULT_PROJECT_ID)
        ),
        api_key=(
            api_key
            or os.environ.get("SENTINEL_API_KEY")
            or (str(file_cfg["api_key"]) if file_cfg.get("api_key") else None)
        ),
    )


def config_as_dict(config: CliConfig) -> dict[str, Any]:
    data = asdict(config)
    return data
