"""Unit tests for fingerprint and leaderboard aggregation."""

from __future__ import annotations

from sentinel_server.models import BenchmarkCell
from sentinel_server.services.benchmarking import build_leaderboard
from sentinel_server.services.fingerprint import (
    build_environment_fingerprint,
    dimensions_key,
    normalize_dimensions,
)


def test_fingerprint_merges_run_and_provided() -> None:
    fp = build_environment_fingerprint(
        run_payload={
            "schema_version": "1.0.0",
            "agent_name": "demo",
            "agent_version": "0.1.0",
            "attributes": {"seed": 42, "sdk_version": "0.1.0"},
        },
        provided={"adapter_version": "forge-0.2", "seed": 99},
    )
    assert fp["schema_version"] == "1.0.0"
    assert fp["sdk_version"] == "0.1.0"
    assert fp["seed"] == 99  # provided wins
    assert fp["adapter_version"] == "forge-0.2"
    assert "sentinel_server_version" in fp


def test_dimensions_key_stable() -> None:
    assert dimensions_key(normalize_dimensions({"b": 1, "a": 2})) == "a=2|b=1"


def test_leaderboard_ranks_and_pairwise() -> None:
    cells = [
        BenchmarkCell(
            project_id="p",
            benchmark_id="b",
            benchmark_version="1.0.0",
            cell_id="c1",
            task_id="t1",
            run_id="r1",
            dimensions={"agent_version": "0.1.0", "model": "a"},
            environment_fingerprint={"seed": 1},
            metrics_snapshot={"wall_ms": 1000, "estimated_cost_usd": 0.01},
            scores_summary={"passed": True, "mean_score": 1.0},
        ),
        BenchmarkCell(
            project_id="p",
            benchmark_id="b",
            benchmark_version="1.0.0",
            cell_id="c2",
            task_id="t1",
            run_id="r2",
            dimensions={"agent_version": "0.2.0", "model": "b"},
            environment_fingerprint={"seed": 1},
            metrics_snapshot={"wall_ms": 800, "estimated_cost_usd": 0.02},
            scores_summary={"passed": False, "mean_score": 0.0},
        ),
    ]
    report = build_leaderboard(cells, baseline_agent_version="0.1.0")
    assert report["group_count"] == 2
    assert report["leaderboard"][0]["rank"] == 1
    assert report["leaderboard"][0]["pass_rate"] == 1.0
    assert len(report["pairwise"]) == 1
    assert report["pairwise"][0]["delta_pass_rate"] == -1.0
