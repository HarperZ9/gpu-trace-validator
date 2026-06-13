from pathlib import Path

from gpu_trace_validator.validator import build_payload, evaluate_assertions, load_trace
from gpu_trace_validator.validator import evaluate_assertions as eval_assertions


def test_assertion_summary_counts() -> None:
    trace = load_trace(Path("tests/fixtures/trace_fail.json"))
    status = evaluate_assertions(trace)
    assert status["failure_count"] == 2


def test_expected_failures_enforced() -> None:
    trace = load_trace(Path("tests/fixtures/trace_fail.json"))
    payload = build_payload(trace, [], 2)
    assert payload["status"] == "pass"


def test_expected_failures_detected() -> None:
    trace = load_trace(Path("tests/fixtures/trace_fail.json"))
    payload = build_payload(trace, [], 1)
    assert payload["status"] == "fail"