"""Unit tests for pure eval engine helpers."""

from __future__ import annotations

import pytest

from sentinel_server.services.eval_engine import (
    EvaluationError,
    apply_threshold,
    evaluate_deterministic,
    evaluate_judge,
    run_context,
)


def _ctx(**kwargs):
    base = run_context(
        run={"status": "succeeded", "run_id": "r1"},
        spans=[
            {
                "kind": "tool",
                "name": "web_search",
                "tool": {"tool_name": "web_search"},
            }
        ],
        events=[{"type": "retry"}],
        metrics={"wall_ms": 1200.0, "retry_count": 1},
    )
    base.update(kwargs)
    return base


def test_run_status_pass() -> None:
    result = evaluate_deterministic({"type": "run_status", "expected": "succeeded"}, _ctx())
    assert result["passed"] is True
    assert result["score_value"] == 1.0


def test_tool_called() -> None:
    result = evaluate_deterministic({"type": "tool_called", "tool_name": "web_search"}, _ctx())
    assert result["passed"] is True
    missing = evaluate_deterministic({"type": "tool_called", "tool_name": "browser"}, _ctx())
    assert missing["passed"] is False


def test_max_retries_and_wall() -> None:
    assert evaluate_deterministic({"type": "max_retries", "max": 1}, _ctx())["passed"] is True
    assert evaluate_deterministic({"type": "max_retries", "max": 0}, _ctx())["passed"] is False
    assert evaluate_deterministic({"type": "max_wall_ms", "max_ms": 2000}, _ctx())["passed"] is True
    assert evaluate_deterministic({"type": "max_wall_ms", "max_ms": 100}, _ctx())["passed"] is False


def test_regex_and_exact_match() -> None:
    ctx = _ctx()
    ctx["run"]["name"] = "answer-user-question"
    assert evaluate_deterministic(
        {"type": "exact_match", "path": "run.name", "expected": "answer-user-question"},
        ctx,
    )["passed"]
    assert evaluate_deterministic(
        {"type": "regex", "path": "run.name", "pattern": r"^answer-"},
        ctx,
    )["passed"]


def test_judge_heuristic() -> None:
    ctx = _ctx()
    ctx["run"]["attributes"] = {"task": "What is Sentinel AI?"}
    result = evaluate_judge(
        {
            "mode": "heuristic",
            "model": "heuristic-v1",
            "prompt_version": "rubric-1",
            "provider": "local",
            "min_pass_ratio": 1.0,
            "checks": [
                {"path": "run.attributes.task", "contains": "Sentinel"},
                {"path": "run.status", "equals": "succeeded"},
            ],
        },
        ctx,
    )
    assert result["passed"] is True
    assert result["details"]["model"] == "heuristic-v1"
    assert result["details"]["prompt_version"] == "rubric-1"


def test_judge_requires_versioned_model() -> None:
    with pytest.raises(EvaluationError):
        evaluate_judge({"mode": "stub", "stub_passed": True}, _ctx())


def test_threshold_min_score() -> None:
    raw = {"score_value": 0.8, "passed": False}
    assert apply_threshold(raw, {"min_score": 0.75}) is True
    assert apply_threshold(raw, {"min_score": 0.9}) is False
