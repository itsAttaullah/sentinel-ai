"""Unit tests for regression threshold engine."""

from __future__ import annotations

from sentinel_server.services.regression_engine import apply_policy


def test_wall_ms_regression_fails() -> None:
    result = apply_policy(
        baseline={"metrics": {"wall_ms": 1000}, "scores": {}},
        candidate={"metrics": {"wall_ms": 2000}, "scores": {}},
        policy={"metrics": {"wall_ms": {"max_increase_ratio": 0.25, "max_increase_abs": 200}}},
    )
    assert result["passed"] is False
    assert result["violation_count"] >= 1


def test_pass_rate_drop_fails() -> None:
    result = apply_policy(
        baseline={"metrics": {}, "scores": {"pass_rate": 1.0}},
        candidate={"metrics": {}, "scores": {"pass_rate": 0.5}},
        policy={"scores": {"pass_rate": {"max_decrease_abs": 0.0}}},
    )
    assert result["passed"] is False


def test_within_thresholds_passes() -> None:
    result = apply_policy(
        baseline={
            "metrics": {"wall_ms": 1000, "retry_count": 1, "success_rate": 1.0},
            "scores": {"pass_rate": 1.0, "mean_score": 1.0},
        },
        candidate={
            "metrics": {"wall_ms": 1100, "retry_count": 1, "success_rate": 1.0},
            "scores": {"pass_rate": 1.0, "mean_score": 0.95},
        },
        policy={
            "metrics": {
                "wall_ms": {"max_increase_ratio": 0.25},
                "retry_count": {"max_increase_abs": 1},
                "success_rate": {"max_decrease_abs": 0.05},
            },
            "scores": {
                "pass_rate": {"max_decrease_abs": 0.0},
                "mean_score": {"max_decrease_abs": 0.1},
            },
        },
    )
    assert result["passed"] is True
