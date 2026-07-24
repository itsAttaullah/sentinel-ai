"""Sentinel CLI entrypoint (`sentinel`)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from sentinel_cli import __version__
from sentinel_cli.client import SentinelApiError, SentinelClient, load_batches_from_path
from sentinel_cli.config import CliConfig, project_config_path, resolve_config, write_config
from sentinel_cli.output import emit, fail

app = typer.Typer(
    name="sentinel",
    help="Sentinel AI CLI — init, upload, and query agent traces.",
    no_args_is_help=True,
    add_completion=False,
)
runs_app = typer.Typer(help="Query runs.")
projects_app = typer.Typer(help="Query projects.")
config_app = typer.Typer(help="Show local CLI configuration.")
app.add_typer(runs_app, name="runs")
app.add_typer(projects_app, name="projects")
app.add_typer(config_app, name="config")


@app.callback()
def _root() -> None:
    """Sentinel AI developer CLI."""


@app.command("version")
def version_cmd(
    json_out: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
) -> None:
    """Print CLI version."""
    emit({"name": "sentinel-cli", "version": __version__}, as_json=json_out, human=__version__)


@app.command("init")
def init_cmd(
    api_url: str = typer.Option("http://localhost:8080", "--api-url"),
    project_id: str = typer.Option("proj_demo", "--project-id"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Create `.sentinel/config.toml` in the current directory."""
    path = project_config_path()
    if path.exists() and not force:
        fail(
            f"Config already exists: {path} (use --force to overwrite)",
            as_json=json_out,
        )
    cfg = CliConfig(api_url=api_url.rstrip("/"), project_id=project_id, api_key=api_key)
    write_config(path, cfg)
    emit(
        {"ok": True, "path": str(path), "config": cfg.to_public_dict()},
        as_json=json_out,
        human=f"Wrote {path}",
    )


@config_app.command("show")
def config_show(
    api_url: Optional[str] = typer.Option(None, "--api-url"),
    project_id: Optional[str] = typer.Option(None, "--project-id"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Show resolved configuration (flags > env > file > defaults)."""
    cfg = resolve_config(api_url=api_url, project_id=project_id, api_key=api_key)
    payload = {
        "config": cfg.to_public_dict(),
        "config_file": str(project_config_path()),
        "config_file_exists": project_config_path().is_file(),
    }
    emit(
        payload,
        as_json=json_out,
        human=(
            f"api_url={cfg.api_url}\n"
            f"project_id={cfg.project_id}\n"
            f"api_key_set={bool(cfg.api_key)}\n"
            f"config_file={payload['config_file']} "
            f"({'exists' if payload['config_file_exists'] else 'missing'})"
        ),
    )


@app.command("whoami")
def whoami_cmd(
    api_url: Optional[str] = typer.Option(None, "--api-url"),
    project_id: Optional[str] = typer.Option(None, "--project-id"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Show config and check API health."""
    cfg = resolve_config(api_url=api_url, project_id=project_id, api_key=api_key)
    try:
        with SentinelClient(cfg) as client:
            health = client.healthz()
    except Exception as exc:  # noqa: BLE001
        fail(
            f"API unreachable at {cfg.api_url}: {exc}",
            as_json=json_out,
            details={"config": cfg.to_public_dict()},
        )
    payload = {"ok": True, "config": cfg.to_public_dict(), "health": health}
    emit(
        payload,
        as_json=json_out,
        human=(
            f"project_id={cfg.project_id}\n"
            f"api_url={cfg.api_url}\n"
            f"health={health.get('status')} version={health.get('version')}"
        ),
    )


@app.command("health")
def health_cmd(
    api_url: Optional[str] = typer.Option(None, "--api-url"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Call GET /healthz."""
    cfg = resolve_config(api_url=api_url, api_key=api_key)
    try:
        with SentinelClient(cfg) as client:
            health = client.healthz()
    except Exception as exc:  # noqa: BLE001
        fail(f"Health check failed: {exc}", as_json=json_out)
    emit(health, as_json=json_out, human=f"status={health.get('status')} version={health.get('version')}")


@app.command("upload")
def upload_cmd(
    path: Path = typer.Argument(..., exists=True, help="JSON/JSONL file or directory"),
    api_url: Optional[str] = typer.Option(None, "--api-url"),
    project_id: Optional[str] = typer.Option(None, "--project-id"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Upload one or more ingest batches to POST /v1/ingest."""
    cfg = resolve_config(api_url=api_url, project_id=project_id, api_key=api_key)
    try:
        batches = load_batches_from_path(path)
    except (OSError, ValueError) as exc:
        fail(str(exc), as_json=json_out)

    results: list[dict] = []
    try:
        with SentinelClient(cfg) as client:
            for index, batch in enumerate(batches):
                # Prefer batch project_id; fall back to config
                if "project_id" not in batch:
                    batch = {**batch, "project_id": cfg.project_id}
                try:
                    accepted = client.ingest(batch)
                    results.append({"index": index, "ok": True, "response": accepted})
                except SentinelApiError as exc:
                    results.append(
                        {
                            "index": index,
                            "ok": False,
                            "status_code": exc.status_code,
                            "error": str(exc),
                            "body": exc.body,
                        }
                    )
    except Exception as exc:  # noqa: BLE001
        fail(f"Upload failed: {exc}", as_json=json_out)

    ok_count = sum(1 for item in results if item["ok"])
    payload = {
        "ok": ok_count == len(results),
        "uploaded": ok_count,
        "failed": len(results) - ok_count,
        "results": results,
    }
    if not payload["ok"]:
        emit(payload, as_json=True)
        raise typer.Exit(code=1)
    emit(
        payload,
        as_json=json_out,
        human=f"Uploaded {ok_count}/{len(results)} batch(es) to {cfg.api_url}",
    )


@projects_app.command("list")
def projects_list(
    api_url: Optional[str] = typer.Option(None, "--api-url"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """List projects."""
    cfg = resolve_config(api_url=api_url, api_key=api_key)
    try:
        with SentinelClient(cfg) as client:
            data = client.list_projects()
    except SentinelApiError as exc:
        fail(str(exc), as_json=json_out, details=exc.body)
    except Exception as exc:  # noqa: BLE001
        fail(str(exc), as_json=json_out)
    items = data.get("items") or []
    human = "\n".join(f"{p.get('id')}\t{p.get('name')}" for p in items) or "(no projects)"
    emit(data, as_json=json_out, human=human)


@runs_app.command("list")
def runs_list(
    project_id: Optional[str] = typer.Option(None, "--project-id"),
    limit: int = typer.Option(50, "--limit", min=1, max=200),
    api_url: Optional[str] = typer.Option(None, "--api-url"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """List runs for a project."""
    cfg = resolve_config(api_url=api_url, project_id=project_id, api_key=api_key)
    try:
        with SentinelClient(cfg) as client:
            data = client.list_runs(cfg.project_id, limit=limit)
    except SentinelApiError as exc:
        fail(str(exc), as_json=json_out, details=exc.body)
    except Exception as exc:  # noqa: BLE001
        fail(str(exc), as_json=json_out)
    items = data.get("items") or []
    lines = []
    for item in items:
        summary = item.get("metrics_summary") or {}
        lines.append(
            f"{item.get('run_id')}\t{item.get('status')}\t"
            f"wall_ms={summary.get('wall_ms')}\tretries={summary.get('retry_count')}"
        )
    emit(data, as_json=json_out, human="\n".join(lines) or "(no runs)")


@runs_app.command("get")
def runs_get(
    run_id: str = typer.Argument(...),
    project_id: Optional[str] = typer.Option(None, "--project-id"),
    include: str = typer.Option("spans,events,metrics", "--include"),
    api_url: Optional[str] = typer.Option(None, "--api-url"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Get a run timeline (and metrics by default)."""
    cfg = resolve_config(api_url=api_url, project_id=project_id, api_key=api_key)
    try:
        with SentinelClient(cfg) as client:
            data = client.get_run(cfg.project_id, run_id, include=include)
    except SentinelApiError as exc:
        fail(str(exc), as_json=json_out, details=exc.body)
    except Exception as exc:  # noqa: BLE001
        fail(str(exc), as_json=json_out)

    run = data.get("run") or {}
    metrics = data.get("metrics") or {}
    human = (
        f"run_id={run.get('run_id')} status={run.get('status')}\n"
        f"spans={len(data.get('spans') or [])} events={len(data.get('events') or [])}\n"
        f"wall_ms={metrics.get('wall_ms')} cost_usd={metrics.get('estimated_cost_usd')} "
        f"retries={metrics.get('retry_count')}"
    )
    emit(data, as_json=json_out, human=human)


@app.command("metrics")
def metrics_cmd(
    project_id: Optional[str] = typer.Option(None, "--project-id"),
    api_url: Optional[str] = typer.Option(None, "--api-url"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Show project-level metric aggregates."""
    cfg = resolve_config(api_url=api_url, project_id=project_id, api_key=api_key)
    try:
        with SentinelClient(cfg) as client:
            data = client.project_metrics(cfg.project_id)
    except SentinelApiError as exc:
        fail(str(exc), as_json=json_out, details=exc.body)
    except Exception as exc:  # noqa: BLE001
        fail(str(exc), as_json=json_out)
    human = (
        f"project_id={data.get('project_id')} runs={data.get('run_count')} "
        f"success_rate={data.get('success_rate')}\n"
        f"wall_ms.avg={(data.get('wall_ms') or {}).get('avg')} "
        f"cost_usd={data.get('total_estimated_cost_usd')} "
        f"retries={data.get('total_retries')}"
    )
    emit(data, as_json=json_out, human=human)


@app.command("serve")
def serve_cmd(
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Print how to start the local Sentinel stack (does not daemonize)."""
    guidance = {
        "compose": "docker compose up --build",
        "api_url": "http://localhost:8080",
        "health": "sentinel health",
        "upload_example": (
            "sentinel upload .\\packages\\schema\\fixtures\\valid\\ingest-batch.hello.json"
        ),
        "notes": [
            "This command prints guidance only; it does not start Docker for you.",
            "Use docker compose from the repository root for the supported local stack.",
        ],
    }
    human = (
        "Start the local stack from the repo root:\n"
        "  docker compose up --build\n\n"
        "Then:\n"
        "  sentinel health\n"
        "  sentinel upload .\\packages\\schema\\fixtures\\valid\\ingest-batch.hello.json\n"
        "  sentinel runs get run_hello_001 --json"
    )
    emit(guidance, as_json=json_out, human=human)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
