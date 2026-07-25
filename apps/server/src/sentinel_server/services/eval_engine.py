"""Pure evaluation helpers: dig paths, deterministic checks, judge heuristics."""

from __future__ import annotations

import json
import re
from typing import Any


class EvaluationError(Exception):
    """Raised when an evaluator config or input is invalid."""


def dig(data: Any, path: str) -> Any:
    """Resolve dotted path with optional list indexes: a.b.0.c"""
    if not path:
        return data
    current = data
    for part in path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
            continue
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
            continue
        return None
    return current


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


def run_context(
    *,
    run: dict[str, Any],
    spans: list[dict[str, Any]],
    events: list[dict[str, Any]],
    metrics: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "run": run,
        "spans": spans,
        "events": events,
        "metrics": metrics or {},
    }


def evaluate_deterministic(
    config: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute a deterministic check.

    config.type one of:
      run_status | exact_match | regex | tool_called | max_retries | max_wall_ms | json_schema_type
    """
    check_type = config.get("type")
    if not check_type:
        raise EvaluationError("deterministic config requires 'type'")

    if check_type == "run_status":
        expected = config.get("expected", "succeeded")
        actual = dig(context, "run.status")
        passed = actual == expected
        return {
            "score_value": 1.0 if passed else 0.0,
            "passed": passed,
            "rationale": f"run.status={actual!r} expected={expected!r}",
            "details": {"actual": actual, "expected": expected},
        }

    if check_type == "exact_match":
        path = config.get("path")
        if not path:
            raise EvaluationError("exact_match requires 'path'")
        expected = config.get("expected")
        actual = dig(context, path)
        passed = actual == expected
        return {
            "score_value": 1.0 if passed else 0.0,
            "passed": passed,
            "rationale": f"{path}={actual!r} expected={expected!r}",
            "details": {"path": path, "actual": actual, "expected": expected},
        }

    if check_type == "regex":
        path = config.get("path")
        pattern = config.get("pattern")
        if not path or not pattern:
            raise EvaluationError("regex requires 'path' and 'pattern'")
        actual = _as_text(dig(context, path))
        matched = re.search(pattern, actual) is not None
        return {
            "score_value": 1.0 if matched else 0.0,
            "passed": matched,
            "rationale": f"regex {pattern!r} on {path}: {'match' if matched else 'no match'}",
            "details": {"path": path, "pattern": pattern, "sample": actual[:500]},
        }

    if check_type == "tool_called":
        tool_name = config.get("tool_name")
        if not tool_name:
            raise EvaluationError("tool_called requires 'tool_name'")
        names: list[str] = []
        for span in context.get("spans") or []:
            if span.get("kind") != "tool":
                continue
            tool = span.get("tool") or {}
            name = tool.get("tool_name") or span.get("name")
            if name:
                names.append(str(name))
        passed = tool_name in names
        return {
            "score_value": 1.0 if passed else 0.0,
            "passed": passed,
            "rationale": (
                f"tool {tool_name!r} {'found' if passed else 'not found'} "
                f"in {names}"
            ),
            "details": {"tool_name": tool_name, "observed": names},
        }

    if check_type == "max_retries":
        max_retries = int(config.get("max", 0))
        retries = int(dig(context, "metrics.retry_count") or 0)
        # also count events if metrics missing
        if dig(context, "metrics.retry_count") is None:
            retries = sum(
                1 for event in (context.get("events") or []) if event.get("type") == "retry"
            )
        passed = retries <= max_retries
        return {
            "score_value": 1.0 if passed else 0.0,
            "passed": passed,
            "rationale": f"retries={retries} max={max_retries}",
            "details": {"retries": retries, "max": max_retries},
        }

    if check_type == "max_wall_ms":
        max_wall = float(config.get("max_ms"))
        wall = dig(context, "metrics.wall_ms")
        if wall is None:
            return {
                "score_value": 0.0,
                "passed": False,
                "rationale": "metrics.wall_ms missing",
                "details": {"max_ms": max_wall},
            }
        passed = float(wall) <= max_wall
        return {
            "score_value": 1.0 if passed else 0.0,
            "passed": passed,
            "rationale": f"wall_ms={wall} max_ms={max_wall}",
            "details": {"wall_ms": wall, "max_ms": max_wall},
        }

    if check_type == "json_schema_type":
        path = config.get("path")
        expected_type = config.get("expected_type")
        if not path or not expected_type:
            raise EvaluationError("json_schema_type requires 'path' and 'expected_type'")
        actual = dig(context, path)
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "object": dict,
            "array": list,
            "null": type(None),
        }
        py_type = type_map.get(expected_type)
        if py_type is None:
            raise EvaluationError(f"unsupported expected_type: {expected_type}")
        passed = isinstance(actual, py_type)
        return {
            "score_value": 1.0 if passed else 0.0,
            "passed": passed,
            "rationale": f"{path} type={type(actual).__name__} expected={expected_type}",
            "details": {"path": path, "actual_type": type(actual).__name__, "expected_type": expected_type},
        }

    raise EvaluationError(f"unknown deterministic type: {check_type}")


def evaluate_judge(
    config: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Versioned judge evaluator.

    Always records model + prompt_version from config.
    Modes:
      - heuristic (default): checklist of {path, contains} / {path, equals}
      - stub: use config.stub_score / stub_passed for tests without an LLM
    """
    mode = config.get("mode", "heuristic")
    model = config.get("model")
    prompt_version = config.get("prompt_version")
    if not model or not prompt_version:
        raise EvaluationError("judge config requires 'model' and 'prompt_version'")

    meta = {
        "mode": mode,
        "model": model,
        "prompt_version": prompt_version,
        "provider": config.get("provider"),
        "rubric": config.get("rubric"),
    }

    if mode == "stub":
        passed = bool(config.get("stub_passed", True))
        score = float(config.get("stub_score", 1.0 if passed else 0.0))
        return {
            "score_value": score,
            "passed": passed,
            "rationale": config.get("stub_rationale") or f"stub judge ({model}@{prompt_version})",
            "details": meta,
        }

    if mode != "heuristic":
        raise EvaluationError(
            f"unsupported judge mode {mode!r}; use 'heuristic' or 'stub' in Phase 7"
        )

    checks = config.get("checks") or []
    if not isinstance(checks, list) or not checks:
        raise EvaluationError("heuristic judge requires non-empty 'checks'")

    results: list[dict[str, Any]] = []
    passed_count = 0
    for index, check in enumerate(checks):
        path = check.get("path")
        if not path:
            raise EvaluationError(f"checks[{index}] missing path")
        actual = dig(context, path)
        ok = True
        note = ""
        if "contains" in check:
            needle = str(check["contains"])
            ok = needle.lower() in _as_text(actual).lower()
            note = f"contains {needle!r}: {ok}"
        elif "equals" in check:
            expected = check["equals"]
            ok = actual == expected
            note = f"equals {expected!r}: {ok}"
        elif "regex" in check:
            pattern = str(check["regex"])
            ok = re.search(pattern, _as_text(actual)) is not None
            note = f"regex {pattern!r}: {ok}"
        else:
            raise EvaluationError(
                f"checks[{index}] needs contains, equals, or regex"
            )
        if ok:
            passed_count += 1
        results.append({"path": path, "ok": ok, "note": note})

    ratio = passed_count / len(checks)
    min_ratio = float(config.get("min_pass_ratio", 1.0))
    passed = ratio >= min_ratio
    return {
        "score_value": round(ratio, 6),
        "passed": passed,
        "rationale": (
            f"judge {model}@{prompt_version}: {passed_count}/{len(checks)} checks "
            f"(min_pass_ratio={min_ratio})"
        ),
        "details": {**meta, "check_results": results, "pass_ratio": ratio},
    }


def apply_threshold(result: dict[str, Any], threshold: dict[str, Any] | None) -> bool:
    """Optionally override pass/fail using suite threshold."""
    if not threshold:
        return bool(result.get("passed"))
    if "pass_if" in threshold:
        return bool(result.get("passed")) is bool(threshold["pass_if"])
    if "min_score" in threshold:
        score = result.get("score_value")
        if score is None:
            return False
        return float(score) >= float(threshold["min_score"])
    return bool(result.get("passed"))
