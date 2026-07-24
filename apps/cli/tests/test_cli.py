"""CLI unit tests (no live server required for most cases)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from sentinel_cli.app import app
from sentinel_cli.client import load_batches_from_path
from sentinel_cli.config import CliConfig, resolve_config, write_config

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["name"] == "sentinel-cli"
    assert "version" in payload


def test_init_and_config_show(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["init", "--api-url", "http://example:8080", "--project-id", "proj_x", "--json"],
    )
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / ".sentinel" / "config.toml").is_file()

    show = runner.invoke(app, ["config", "show", "--json"])
    assert show.exit_code == 0
    payload = json.loads(show.stdout)
    assert payload["config"]["api_url"] == "http://example:8080"
    assert payload["config"]["project_id"] == "proj_x"


def test_init_refuses_overwrite(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["init", "--json"]).exit_code == 0
    again = runner.invoke(app, ["init", "--json"])
    assert again.exit_code == 1


def test_load_batches_json_and_jsonl(tmp_path: Path) -> None:
    batch = {
        "schema_version": "1.0.0",
        "project_id": "p",
        "runs": [
            {
                "schema_version": "1.0.0",
                "project_id": "p",
                "run_id": "r1",
                "status": "running",
                "started_at": "2026-07-23T09:15:30.000Z",
            }
        ],
    }
    single = tmp_path / "one.json"
    single.write_text(json.dumps(batch), encoding="utf-8")
    assert len(load_batches_from_path(single)) == 1

    jsonl = tmp_path / "many.jsonl"
    jsonl.write_text(json.dumps(batch) + "\n" + json.dumps(batch) + "\n", encoding="utf-8")
    assert len(load_batches_from_path(jsonl)) == 2


def test_resolve_config_env_overrides_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    write_config(
        tmp_path / ".sentinel" / "config.toml",
        CliConfig(api_url="http://file:8080", project_id="from_file"),
    )
    monkeypatch.setenv("SENTINEL_API_URL", "http://env:9090")
    monkeypatch.setenv("SENTINEL_PROJECT_ID", "from_env")
    cfg = resolve_config()
    assert cfg.api_url == "http://env:9090"
    assert cfg.project_id == "from_env"


def test_serve_prints_guidance() -> None:
    result = runner.invoke(app, ["serve", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "compose" in payload
