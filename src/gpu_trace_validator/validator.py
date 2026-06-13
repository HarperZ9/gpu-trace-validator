from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from importlib import resources

DEFAULT_SCHEMA = (
    resources.files(__name__.rsplit(".", 1)[0] + ".schemas")
    if False
    else Path(__file__).resolve().parent / "schemas" / "gpu_trace.schema.json"
)


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_trace(path: str | Path) -> dict[str, Any]:
    trace = load_json(path)
    if not isinstance(trace, dict):
        raise ValueError("GPU trace root must be a JSON object")
    return trace


def _assertion_summary(event: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "seq",
        "frame_id",
        "pass_id",
        "stage",
        "slot",
        "resource_id",
        "assertion",
        "verdict",
        "provenance",
    )
    return {key: event[key] for key in keys if key in event}


def evaluate_assertions(trace: dict[str, Any]) -> dict[str, Any]:
    events = trace.get("events", []) if isinstance(trace.get("events", []), list) else []
    assertion_events = [
        event for event in events if isinstance(event, dict) and event.get("event_type") == "assertion"
    ]
    failures = [_assertion_summary(event) for event in assertion_events if event.get("verdict") == "fail"]
    unknowns = [_assertion_summary(event) for event in assertion_events if event.get("verdict") == "unknown"]
    status = "fail" if failures else "unknown" if unknowns else "pass"
    return {
        "status": status,
        "assertion_count": len(assertion_events),
        "failure_count": len(failures),
        "unknown_count": len(unknowns),
        "failures": failures,
        "unknowns": unknowns,
    }


def build_payload(
    trace: dict[str, Any],
    schema_errors: list[str],
    expected_failures: int | None,
) -> dict[str, Any]:
    assertion_report = evaluate_assertions(trace)
    errors = list(schema_errors)
    failure_count = assertion_report["failure_count"]

    if expected_failures is None and failure_count:
        errors.append(f"observed {failure_count} assertion failure(s)")
    elif expected_failures is not None and failure_count != expected_failures:
        errors.append(f"expected {expected_failures} assertion failure(s), observed {failure_count}")

    return {
        "status": "fail" if errors else "pass",
        "trace_id": trace.get("trace_id", ""),
        "schema_errors": schema_errors,
        "assertions": assertion_report,
        "errors": errors,
    }
