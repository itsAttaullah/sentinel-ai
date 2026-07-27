"""Conformance tests for official adapters."""

from __future__ import annotations

from sentinel_adapter_conformance import run_conformance
from sentinel_adapter_custom import CustomAdapter
from sentinel_adapter_langgraph import LangGraphAdapter


def test_custom_adapter_conformance() -> None:
    report = run_conformance(CustomAdapter())
    assert report.passed, report.checks


def test_langgraph_adapter_conformance() -> None:
    report = run_conformance(LangGraphAdapter())
    assert report.passed, report.checks


def test_metadata_to_dict() -> None:
    meta = CustomAdapter().metadata.to_dict()
    assert meta["framework"] == "custom"
    assert meta["schema_version"]
