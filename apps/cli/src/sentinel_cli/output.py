"""Output helpers for human and JSON modes."""

from __future__ import annotations

import json
from typing import Any

import typer


def emit(data: Any, *, as_json: bool, human: str | None = None) -> None:
    if as_json:
        typer.echo(json.dumps(data, indent=2, default=str))
        return
    if human is not None:
        typer.echo(human)
        return
    if isinstance(data, str):
        typer.echo(data)
    else:
        typer.echo(json.dumps(data, indent=2, default=str))


def fail(message: str, *, as_json: bool, code: int = 1, details: Any = None) -> None:
    payload = {"ok": False, "error": message}
    if details is not None:
        payload["details"] = details
    if as_json:
        typer.echo(json.dumps(payload, indent=2, default=str), err=True)
    else:
        typer.secho(message, fg=typer.colors.RED, err=True)
    raise typer.Exit(code=code)
