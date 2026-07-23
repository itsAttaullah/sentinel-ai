"""JSON Schema validation against packages/schema v1."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource

from sentinel_server.config import get_settings


class SchemaValidationError(Exception):
    def __init__(self, message: str, *, errors: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.errors = errors or []


@lru_cache
def _load_registry(schema_dir: str) -> tuple[Registry, dict[str, Any]]:
    directory = Path(schema_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"Schema directory not found: {directory}")

    registry: Registry = Registry()
    schemas: dict[str, Any] = {}
    for path in sorted(directory.glob("*.schema.json")):
        contents = json.loads(path.read_text(encoding="utf-8"))
        schema_id = contents.get("$id") or path.name
        schemas[path.name] = contents
        registry = registry.with_resource(schema_id, Resource.from_contents(contents))
        # Also allow lookup by filename for local $ref like "run.schema.json"
        registry = registry.with_resource(path.name, Resource.from_contents(contents))
    return registry, schemas


def get_ingest_validator() -> Draft202012Validator:
    settings = get_settings()
    registry, schemas = _load_registry(str(settings.schema_dir.resolve()))
    schema = schemas["ingest-batch.schema.json"]
    return Draft202012Validator(schema, registry=registry)


def validate_ingest_batch(payload: Any) -> None:
    validator = get_ingest_validator()
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if not errors:
        return
    details = [
        {
            "message": err.message,
            "path": list(err.path),
            "validator": err.validator,
        }
        for err in errors[:25]
    ]
    raise SchemaValidationError(
        "Ingest batch failed JSON Schema validation",
        errors=details,
    )


def assert_project_consistency(batch: dict[str, Any]) -> None:
    """Ensure nested entities share the batch project_id."""
    project_id = batch.get("project_id")
    mismatches: list[dict[str, Any]] = []
    for collection in ("runs", "spans", "events"):
        for index, item in enumerate(batch.get(collection) or []):
            if item.get("project_id") != project_id:
                mismatches.append(
                    {
                        "collection": collection,
                        "index": index,
                        "expected": project_id,
                        "actual": item.get("project_id"),
                    }
                )
    if mismatches:
        raise SchemaValidationError(
            "Nested entity project_id does not match batch project_id",
            errors=mismatches,
        )
