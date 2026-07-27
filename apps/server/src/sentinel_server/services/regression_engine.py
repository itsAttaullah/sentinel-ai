"""Pure regression threshold evaluation (CI gates)."""

from __future__ import annotations

from typing import Any


def apply_policy(
    *,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """
    Compare candidate snapshot to baseline using a threshold policy.

    Policy shape (all optional sections):
      metrics.<key>: { max_increase_ratio, max_increase_abs, max_decrease_abs, min_absolute, max_absolute }
      scores.<key>: same
      require_candidate_eval_pass: bool
    """
    violations: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []

    baseline_metrics = baseline.get("metrics") or {}
    candidate_metrics = candidate.get("metrics") or {}
    for key, rules in (policy.get("metrics") or {}).items():
        result = _compare_number(
            key=f"metrics.{key}",
            baseline_value=_as_float(baseline_metrics.get(key)),
            candidate_value=_as_float(candidate_metrics.get(key)),
            rules=rules or {},
            higher_is_worse=key
            in {"wall_ms", "estimated_cost_usd", "retry_count", "tokens_in", "tokens_out"},
        )
        comparisons.append(result)
        if not result["passed"]:
            violations.append(result)

    baseline_scores = baseline.get("scores") or {}
    candidate_scores = candidate.get("scores") or {}
    for key, rules in (policy.get("scores") or {}).items():
        higher_is_worse = False
        result = _compare_number(
            key=f"scores.{key}",
            baseline_value=_as_float(baseline_scores.get(key)),
            candidate_value=_as_float(candidate_scores.get(key)),
            rules=rules or {},
            higher_is_worse=higher_is_worse,
        )
        comparisons.append(result)
        if not result["passed"]:
            violations.append(result)

    if policy.get("require_candidate_eval_pass"):
        cand_pass = candidate_scores.get("pass_rate")
        # also accept boolean passed
        passed_flag = candidate_scores.get("passed")
        ok = True
        detail = ""
        if passed_flag is False:
            ok = False
            detail = "candidate scores.passed is false"
        elif cand_pass is not None and float(cand_pass) < 1.0:
            ok = False
            detail = f"candidate scores.pass_rate={cand_pass} < 1.0"
        check = {
            "key": "require_candidate_eval_pass",
            "passed": ok,
            "baseline": None,
            "candidate": {"pass_rate": cand_pass, "passed": passed_flag},
            "delta": None,
            "message": detail or "ok",
        }
        comparisons.append(check)
        if not ok:
            violations.append(check)

    return {
        "passed": len(violations) == 0,
        "violation_count": len(violations),
        "violations": violations,
        "comparisons": comparisons,
        "baseline": baseline,
        "candidate": candidate,
    }


def _compare_number(
    *,
    key: str,
    baseline_value: float | None,
    candidate_value: float | None,
    rules: dict[str, Any],
    higher_is_worse: bool,
) -> dict[str, Any]:
    if candidate_value is None:
        return {
            "key": key,
            "passed": False,
            "baseline": baseline_value,
            "candidate": None,
            "delta": None,
            "message": f"{key}: candidate value missing",
        }
    if baseline_value is None:
        # No baseline → only absolute bounds apply
        passed = True
        messages: list[str] = []
        if "min_absolute" in rules and candidate_value < float(rules["min_absolute"]):
            passed = False
            messages.append(
                f"candidate {candidate_value} < min_absolute {rules['min_absolute']}"
            )
        if "max_absolute" in rules and candidate_value > float(rules["max_absolute"]):
            passed = False
            messages.append(
                f"candidate {candidate_value} > max_absolute {rules['max_absolute']}"
            )
        return {
            "key": key,
            "passed": passed,
            "baseline": None,
            "candidate": candidate_value,
            "delta": None,
            "message": "; ".join(messages) if messages else "ok (no baseline)",
        }

    delta = candidate_value - baseline_value
    passed = True
    messages = []

    if "min_absolute" in rules and candidate_value < float(rules["min_absolute"]):
        passed = False
        messages.append(
            f"candidate {candidate_value} < min_absolute {rules['min_absolute']}"
        )
    if "max_absolute" in rules and candidate_value > float(rules["max_absolute"]):
        passed = False
        messages.append(
            f"candidate {candidate_value} > max_absolute {rules['max_absolute']}"
        )

    if higher_is_worse:
        if "max_increase_abs" in rules and delta > float(rules["max_increase_abs"]):
            passed = False
            messages.append(
                f"increase {delta} > max_increase_abs {rules['max_increase_abs']}"
            )
        if "max_increase_ratio" in rules and baseline_value != 0:
            ratio = delta / abs(baseline_value)
            if ratio > float(rules["max_increase_ratio"]):
                passed = False
                messages.append(
                    f"increase ratio {ratio:.6f} > max_increase_ratio "
                    f"{rules['max_increase_ratio']}"
                )
    else:
        # lower is worse (scores, success_rate, pass_rate)
        if "max_decrease_abs" in rules and (-delta) > float(rules["max_decrease_abs"]):
            passed = False
            messages.append(
                f"decrease {-delta} > max_decrease_abs {rules['max_decrease_abs']}"
            )
        if "max_decrease_ratio" in rules and baseline_value != 0:
            ratio = (-delta) / abs(baseline_value)
            if ratio > float(rules["max_decrease_ratio"]):
                passed = False
                messages.append(
                    f"decrease ratio {ratio:.6f} > max_decrease_ratio "
                    f"{rules['max_decrease_ratio']}"
                )

    return {
        "key": key,
        "passed": passed,
        "baseline": baseline_value,
        "candidate": candidate_value,
        "delta": round(delta, 6),
        "message": "; ".join(messages) if messages else "ok",
    }


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def default_ci_policy() -> dict[str, Any]:
    """Sensible default gate for CI (deterministic-friendly)."""
    return {
        "metrics": {
            "wall_ms": {"max_increase_ratio": 0.25, "max_increase_abs": 2000},
            "estimated_cost_usd": {"max_increase_ratio": 0.25},
            "retry_count": {"max_increase_abs": 2},
            "success_rate": {"max_decrease_abs": 0.05, "min_absolute": 0.8},
        },
        "scores": {
            "pass_rate": {"max_decrease_abs": 0.0, "min_absolute": 1.0},
            "mean_score": {"max_decrease_abs": 0.1},
        },
        "require_candidate_eval_pass": False,
    }
