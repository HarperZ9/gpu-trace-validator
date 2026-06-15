from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from importlib import resources

DEFAULT_SCHEMA = (
    resources.files(__name__.rsplit(".", 1)[0] + ".schemas")
    if False
    else Path(__file__).resolve().parent / "schemas" / "gpu_trace.schema.json"
)
MAX_FIELD_LENGTH = 240
REDACTION_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\b(bearer|token|api[_-]?key|password|secret)\s*[:=]\s*\S+"),
    re.compile(r"\b[A-Za-z]:\\[^\s'\"<>]+"),
    re.compile(r"(?<!\w)/(?:Users|home|tmp|dev|var|etc)/[^\s'\"<>]+"),
)


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_trace(path: str | Path) -> dict[str, Any]:
    trace = load_json(path)
    if not isinstance(trace, dict):
        raise ValueError("GPU trace root must be a JSON object")
    return trace


def scrub_text(value: str, max_length: int = MAX_FIELD_LENGTH) -> str:
    text = value.replace("\x00", " ")
    for pattern in REDACTION_PATTERNS:
        text = pattern.sub("<redacted>", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_length:
        text = text[: max_length - 3].rstrip() + "..."
    return text


def scrub_value(value: Any) -> Any:
    if isinstance(value, str):
        return scrub_text(value)
    return value


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
    return {key: scrub_value(event[key]) for key in keys if key in event}


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
    schema_errors = [scrub_text(error) for error in schema_errors]
    errors = list(schema_errors)
    failure_count = assertion_report["failure_count"]
    expectation = {
        "expected_failures": expected_failures,
        "observed_failures": failure_count,
        "status": "not-checked" if expected_failures is None else "pass",
    }

    if expected_failures is None and failure_count:
        errors.append(f"observed {failure_count} assertion failure(s)")
    elif expected_failures is not None and failure_count != expected_failures:
        expectation["status"] = "fail"
        errors.append(f"expected {expected_failures} assertion failure(s), observed {failure_count}")

    return {
        "status": "fail" if errors else "pass",
        "trace_id": scrub_value(trace.get("trace_id", "")),
        "schema_errors": schema_errors,
        "assertions": assertion_report,
        "assertion_expectation": expectation,
        "errors": errors,
    }
