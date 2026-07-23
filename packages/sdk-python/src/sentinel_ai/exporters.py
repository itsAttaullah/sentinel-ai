"""Trace exporters."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable, Sequence

logger = logging.getLogger(__name__)


class Exporter(ABC):
    """Exports an IngestBatch dict to a backend."""

    @abstractmethod
    def export(self, batch: dict[str, Any]) -> None:
        raise NotImplementedError

    def shutdown(self) -> None:
        """Optional cleanup hook."""


class ConsoleExporter(Exporter):
    """Print batches as JSON (debug)."""

    def export(self, batch: dict[str, Any]) -> None:
        print(json.dumps(batch, indent=2, ensure_ascii=False))


class FileExporter(Exporter):
    """Append one JSON object per line (JSONL of IngestBatch)."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def export(self, batch: dict[str, Any]) -> None:
        line = json.dumps(batch, ensure_ascii=False, separators=(",", ":"))
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


class HttpExporter(Exporter):
    """
    POST batches to Sentinel ingest.

    Default endpoint matches the OpenAPI stub (`POST /v1/ingest`).
    The server is implemented in a later phase; this client is ready early.
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:8080/v1/ingest",
        *,
        api_key: str | None = None,
        timeout_seconds: float = 10.0,
        max_retries: int = 3,
        backoff_seconds: float = 0.5,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    def export(self, batch: dict[str, Any]) -> None:
        payload = json.dumps(batch, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["X-Sentinel-Api-Key"] = self.api_key

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            request = urllib.request.Request(
                self.endpoint,
                data=payload,
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    # 2xx is success; body ignored for now
                    if 200 <= response.status < 300:
                        return
                    last_error = RuntimeError(
                        f"Unexpected status {response.status} from {self.endpoint}"
                    )
            except urllib.error.HTTPError as exc:
                # 4xx (except 408/429) should not retry forever
                if exc.code in {408, 429} or exc.code >= 500:
                    last_error = exc
                else:
                    raise
            except Exception as exc:  # noqa: BLE001 — network errors are varied
                last_error = exc

            if attempt < self.max_retries:
                time.sleep(self.backoff_seconds * attempt)

        assert last_error is not None
        raise last_error


class MultiExporter(Exporter):
    """Fan-out to multiple exporters; continues if one fails (logs and re-raises last)."""

    def __init__(self, exporters: Sequence[Exporter]) -> None:
        if not exporters:
            raise ValueError("MultiExporter requires at least one exporter")
        self.exporters = list(exporters)

    def export(self, batch: dict[str, Any]) -> None:
        errors: list[Exception] = []
        for exporter in self.exporters:
            try:
                exporter.export(batch)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Exporter %s failed", type(exporter).__name__)
                errors.append(exc)
        if errors:
            raise errors[-1]

    def shutdown(self) -> None:
        for exporter in self.exporters:
            exporter.shutdown()


def as_exporter_list(exporter: Exporter | Iterable[Exporter] | None) -> list[Exporter]:
    if exporter is None:
        return []
    if isinstance(exporter, Exporter):
        return [exporter]
    return list(exporter)
