"""HTTP client for the Sentinel control plane."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from sentinel_cli.config import CliConfig


class SentinelApiError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, body: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class SentinelClient:
    def __init__(self, config: CliConfig, *, timeout: float = 30.0) -> None:
        self.config = config
        headers: dict[str, str] = {"Accept": "application/json"}
        if config.api_key:
            headers["X-Sentinel-Api-Key"] = config.api_key
        self._client = httpx.Client(
            base_url=config.api_url,
            headers=headers,
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> SentinelClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._client.request(method, path, **kwargs)
        if response.status_code >= 400:
            try:
                body = response.json()
            except Exception:  # noqa: BLE001
                body = response.text
            raise SentinelApiError(
                f"{method} {path} failed with {response.status_code}",
                status_code=response.status_code,
                body=body,
            )
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def healthz(self) -> dict[str, Any]:
        return self._request("GET", "/healthz")

    def readyz(self) -> dict[str, Any]:
        return self._request("GET", "/readyz")

    def ingest(self, batch: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/ingest", json=batch)

    def list_projects(self) -> dict[str, Any]:
        return self._request("GET", "/v1/projects")

    def list_runs(self, project_id: str, *, limit: int = 50) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/v1/projects/{project_id}/runs",
            params={"limit": limit},
        )

    def get_run(
        self,
        project_id: str,
        run_id: str,
        *,
        include: str = "spans,events,metrics",
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/v1/projects/{project_id}/runs/{run_id}",
            params={"include": include},
        )

    def project_metrics(self, project_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/projects/{project_id}/metrics")


def load_batches_from_path(path: Path) -> list[dict[str, Any]]:
    """Load one or more IngestBatch objects from a file or directory."""
    if path.is_dir():
        files = sorted(
            [*path.glob("*.json"), *path.glob("*.jsonl"), *path.glob("*.JSON"), *path.glob("*.JSONL")]
        )
        if not files:
            raise FileNotFoundError(f"No .json/.jsonl files in directory: {path}")
        batches: list[dict[str, Any]] = []
        for file in files:
            batches.extend(load_batches_from_path(file))
        return batches

    if not path.is_file():
        raise FileNotFoundError(f"Path not found: {path}")

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"File is empty: {path}")

    if path.suffix.lower() == ".jsonl":
        batches = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON") from exc
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            batches.append(item)
        return batches

    data = json.loads(text)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        if not all(isinstance(item, dict) for item in data):
            raise ValueError(f"{path}: JSON array must contain objects")
        return data
    raise ValueError(f"{path}: expected JSON object or array of objects")
