"""Buffered export of runs/spans/events as IngestBatch payloads."""

from __future__ import annotations

import atexit
import logging
import threading
from typing import Any

from sentinel_ai._utils import new_id, omit_none, utc_now_iso
from sentinel_ai._version import SCHEMA_VERSION
from sentinel_ai.exporters import Exporter

logger = logging.getLogger(__name__)


class BatchBuffer:
    """
    Collects entities and flushes IngestBatch dicts to exporters.

    Flush triggers:
    - explicit flush()
    - entity count reaches max_batch_size
    - optional background interval (when enabled)
    """

    def __init__(
        self,
        *,
        project_id: str,
        exporters: list[Exporter],
        max_batch_size: int = 64,
        flush_interval_seconds: float | None = 2.0,
    ) -> None:
        self.project_id = project_id
        self.exporters = exporters
        self.max_batch_size = max_batch_size
        self.flush_interval_seconds = flush_interval_seconds

        self._lock = threading.RLock()
        self._runs: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._events: list[dict[str, Any]] = []
        self._closed = False

        self._timer: threading.Timer | None = None
        if flush_interval_seconds and exporters:
            self._arm_timer()

        atexit.register(self._atexit_flush)

    def _entity_count(self) -> int:
        return len(self._runs) + len(self._spans) + len(self._events)

    def add_run(self, payload: dict[str, Any]) -> None:
        self._add("runs", payload)

    def add_span(self, payload: dict[str, Any]) -> None:
        self._add("spans", payload)

    def add_event(self, payload: dict[str, Any]) -> None:
        self._add("events", payload)

    def _add(self, kind: str, payload: dict[str, Any]) -> None:
        with self._lock:
            if self._closed:
                raise RuntimeError("BatchBuffer is shut down")
            getattr(self, f"_{kind}").append(payload)
            should_flush = self._entity_count() >= self.max_batch_size
        if should_flush:
            self.flush()

    def flush(self) -> None:
        with self._lock:
            if self._entity_count() == 0:
                return
            batch = self._build_batch_locked()
            self._runs.clear()
            self._spans.clear()
            self._events.clear()

        for exporter in self.exporters:
            exporter.export(batch)

    def shutdown(self) -> None:
        with self._lock:
            self._closed = True
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
        self.flush()
        for exporter in self.exporters:
            exporter.shutdown()

    def _build_batch_locked(self) -> dict[str, Any]:
        batch = omit_none(
            {
                "schema_version": SCHEMA_VERSION,
                "project_id": self.project_id,
                "batch_id": new_id("batch_"),
                "sent_at": utc_now_iso(),
                "runs": list(self._runs) or None,
                "spans": list(self._spans) or None,
                "events": list(self._events) or None,
            }
        )
        # Ensure at least one non-empty collection key exists for schema anyOf.
        if "runs" not in batch and "spans" not in batch and "events" not in batch:
            batch["runs"] = []
        return batch

    def _arm_timer(self) -> None:
        assert self.flush_interval_seconds is not None
        self._timer = threading.Timer(self.flush_interval_seconds, self._timer_flush)
        self._timer.daemon = True
        self._timer.start()

    def _timer_flush(self) -> None:
        try:
            self.flush()
        except Exception:  # noqa: BLE001
            logger.exception("Background flush failed")
        with self._lock:
            if not self._closed and self.flush_interval_seconds:
                self._arm_timer()

    def _atexit_flush(self) -> None:
        try:
            if not self._closed:
                self.shutdown()
        except Exception:  # noqa: BLE001
            logger.exception("atexit flush failed")
