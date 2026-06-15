from pathlib import Path

from jsonschema import Draft202012Validator

from gpu_trace_validator.validator import DEFAULT_SCHEMA, build_payload, evaluate_assertions, load_json, load_trace


def test_assertion_summary_counts() -> None:
    trace = load_trace(Path("tests/fixtures/trace_fail.json"))
    status = evaluate_assertions(trace)
    assert status["failure_count"] == 2


def test_expected_failures_enforced() -> None:
    trace = load_trace(Path("tests/fixtures/trace_fail.json"))
    payload = build_payload(trace, [], 2)
    assert payload["status"] == "pass"
    assert payload["assertion_expectation"]["status"] == "pass"


def test_expected_failures_detected() -> None:
    trace = load_trace(Path("tests/fixtures/trace_fail.json"))
    payload = build_payload(trace, [], 1)
    assert payload["status"] == "fail"
    assert payload["assertion_expectation"]["status"] == "fail"


def test_bundled_fixtures_match_schema() -> None:
    schema = load_json(DEFAULT_SCHEMA)
    validator = Draft202012Validator(schema)
    for fixture in ("trace_pass.json", "trace_fail.json"):
        trace = load_trace(Path("tests/fixtures") / fixture)
        assert list(validator.iter_errors(trace)) == []


def test_payload_redacts_trace_and_assertion_fields() -> None:
    synthetic = "ghp_" + ("A" * 36)
    trace = {
        "trace_id": "C:\\Users\\Zain\\trace.json",
        "events": [
            {
                "event_type": "assertion",
                "seq": 1,
                "frame_id": 1,
                "assertion": f"token={synthetic}",
                "verdict": "fail",
                "provenance": "/Users/zain/private/trace.json",
            }
        ],
    }

    payload = build_payload(trace, [f"schema saw token={synthetic}"], None)
    rendered = str(payload)

    assert "ghp_" not in rendered
    assert "C:\\Users" not in rendered
    assert "/Users/zain" not in rendered
    assert "<redacted>" in rendered
