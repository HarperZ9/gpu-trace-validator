"""The art gate settles whether a drawing fits its columns and matches its spec. It
cannot settle whether the drawing is true of the code, because both sides are derived
from the same JSON. So this file drives the validator instead: every claim the three
drawings make is asserted here against running code, and a claim that stops holding
fails the suite rather than staying on the page."""

import json
from pathlib import Path

from gpu_trace_validator.cli import main
from gpu_trace_validator.validator import (
    MAX_FIELD_LENGTH,
    build_payload,
    evaluate_assertions,
    scrub_text,
)

_REPO = Path(__file__).resolve().parents[1]
_SPEC = _REPO / "docs" / "art" / "gpu-trace-validator.art.json"
_SCHEMA = _REPO / "src" / "gpu_trace_validator" / "schemas" / "gpu_trace.schema.json"


def _trace(**over) -> dict:
    base = {
        "trace_id": "art-fixture",
        "schema_version": "1",
        "source": {"kind": "manual-fixture", "path_or_handle": "tests/fixtures"},
        "frames": [{"frame_id": 0}],
        "resources": [{"resource_id": "rt0", "kind": "texture2d"}],
        "events": [],
    }
    base.update(over)
    return base


def _event(seq: int, verdict: str | None = None, event_type: str = "assertion", **over) -> dict:
    event = {"seq": seq, "frame_id": 0, "event_type": event_type}
    if verdict is not None:
        event["verdict"] = verdict
    event.update(over)
    return event


def _run(tmp_path, capsys, payload, *flags) -> tuple[int, dict]:
    path = tmp_path / "trace.json"
    text = payload if isinstance(payload, str) else json.dumps(payload)
    path.write_text(text, encoding="utf-8")
    code = main([str(path), "--json", *flags])
    return code, json.loads(capsys.readouterr().out)


def _raw(tmp_path, capsys, payload) -> tuple[int, str]:
    path = tmp_path / "trace.json"
    text = payload if isinstance(payload, str) else json.dumps(payload)
    path.write_text(text, encoding="utf-8")
    code = main([str(path)])
    return code, capsys.readouterr().out


def test_six_fields_are_required_at_the_root_and_a_seventh_is_named(tmp_path, capsys) -> None:
    """The drawing says six required fields and an unexpected property named rather
    than ignored. Both halves are checked here, because a schema that quietly
    accepted an extra key would still render the same picture."""
    trace = _trace()
    assert sorted(trace) == ["events", "frames", "resources", "schema_version", "source", "trace_id"]

    for field in list(trace):
        short = {key: value for key, value in trace.items() if key != field}
        code, payload = _run(tmp_path, capsys, short)
        assert code == 1, field
        assert any(field in error for error in payload["schema_errors"]), field

    code, payload = _run(tmp_path, capsys, _trace(vendor_notes="anything"))
    assert code == 1
    assert any("vendor_notes" in error for error in payload["schema_errors"])


def test_an_unexpected_property_is_refused_inside_a_frame_and_an_event_too(tmp_path, capsys) -> None:
    """The card says unknown properties are refused at the root, in a frame, in a
    resource and in an event, and named with the path that carried them. Four
    places, so four cases."""
    cases = {
        "frames": _trace(frames=[{"frame_id": 0, "ns": 12}]),
        "resources": _trace(resources=[{"resource_id": "r", "kind": "buffer", "ns": 1}]),
        "events": _trace(events=[_event(0, "pass", ns=1)]),
    }
    for where, trace in cases.items():
        code, payload = _run(tmp_path, capsys, trace)
        assert code == 1, where
        assert any(error.startswith(where + "/0:") for error in payload["schema_errors"]), where

    code, payload = _run(tmp_path, capsys, _trace(ns=1))
    assert code == 1
    assert any(error.startswith("<root>:") for error in payload["schema_errors"])


def test_a_root_that_is_not_an_object_is_refused_before_any_check(tmp_path, capsys) -> None:
    """The third outcome of the first drawing. A list at the root never reaches the
    schema, so there is no receipt to print and the exit code carries the news."""
    code, output = _raw(tmp_path, capsys, [{"trace_id": "x"}])
    assert code == 1
    assert "must be a JSON object" in output
    assert "gpu_trace_validation:" not in output

    code, output = _raw(tmp_path, capsys, "{not json at all")
    assert code == 1
    assert "error:" in output


def test_three_closed_sets_refuse_a_value_that_is_not_on_the_list(tmp_path, capsys) -> None:
    """Four capture kinds, nine event types, four verdicts. The drawing counts all
    three, so all three are counted here against the schema that ships."""
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    properties = schema["properties"]
    assert len(properties["source"]["properties"]["kind"]["enum"]) == 4
    events = properties["events"]["items"]["properties"]
    assert len(events["event_type"]["enum"]) == 9
    assert len(events["verdict"]["enum"]) == 4

    off_list = (
        _trace(source={"kind": "guesswork", "path_or_handle": "x"}),
        _trace(events=[_event(0, event_type="teleport")]),
        _trace(events=[_event(0, "maybe")]),
    )
    for trace in off_list:
        code, payload = _run(tmp_path, capsys, trace)
        assert code == 1
        assert payload["schema_errors"]


def test_only_the_assertion_event_carries_a_verdict_that_counts() -> None:
    """Nine event kinds share one shape, so a draw call can hold a verdict field and
    the schema will take it. The report reads verdicts from assertion events alone,
    which is what the drawing claims when it says one of the nine."""
    hidden = _trace(events=[_event(0, "fail", event_type="draw")])
    report = evaluate_assertions(hidden)
    assert report["assertion_count"] == 0
    assert report["status"] == "pass"

    named = _trace(events=[_event(0, "fail")])
    assert evaluate_assertions(named)["failure_count"] == 1


def test_two_of_the_four_verdicts_are_counted_and_the_other_two_are_not() -> None:
    """The card gives not-applicable its own row: counted as neither a failure nor an
    unknown, so it lands with the passes."""
    for verdict, field in {"fail": "failure_count", "unknown": "unknown_count"}.items():
        report = evaluate_assertions(_trace(events=[_event(0, verdict)]))
        assert report[field] == 1, verdict

    for verdict in ("pass", "not-applicable"):
        report = evaluate_assertions(_trace(events=[_event(0, verdict)]))
        assert report["status"] == "pass", verdict
        assert report["failure_count"] == 0 and report["unknown_count"] == 0, verdict


def test_an_unknown_verdict_reads_unknown_and_the_run_still_exits_zero(tmp_path, capsys) -> None:
    """The accented row of the card. Two statuses are in play: the assertion report
    says what the trace recorded, the run says whether anything was refused, and
    only the second one sets the exit code."""
    trace = _trace(events=[_event(0, "unknown"), _event(1, "pass")])
    code, payload = _run(tmp_path, capsys, trace)
    assert code == 0
    assert payload["assertions"]["status"] == "unknown"
    assert payload["status"] == "pass"
    assert payload["errors"] == []


def test_a_trace_that_asserts_nothing_reports_pass(tmp_path, capsys) -> None:
    """A row of the card, and an honest null. Draws and presents with no assertion
    among them refuse nothing, so nothing fails."""
    quiet = _trace(events=[_event(0, event_type="draw"), _event(1, event_type="present")])
    code, payload = _run(tmp_path, capsys, quiet)
    assert code == 0
    assert payload["assertions"]["assertion_count"] == 0
    assert payload["status"] == "pass"


def test_a_count_that_matches_turns_a_failing_fixture_into_a_pass() -> None:
    """A check that cannot fail proves nothing, so a fixture recorded to break is
    worth keeping. Naming the number up front is what makes it a check."""
    trace = _trace(events=[_event(0, "fail"), _event(1, "fail")])
    payload = build_payload(trace, [], 2)
    assert payload["status"] == "pass"
    assert payload["assertion_expectation"]["status"] == "pass"
    assert payload["assertion_expectation"]["observed_failures"] == 2


def test_the_comparison_runs_in_both_directions() -> None:
    """Fewer failures than expected is refused exactly as firmly as more, which is
    the sentence the drawing carries on its return edge."""
    two = _trace(events=[_event(0, "fail"), _event(1, "fail")])
    for expected in (1, 3):
        payload = build_payload(two, [], expected)
        assert payload["status"] == "fail", expected
        assert payload["assertion_expectation"]["status"] == "fail", expected


def test_with_no_count_given_the_expectation_is_not_checked_and_a_failure_fails() -> None:
    """The third outcome of the second drawing, and the first row of the card."""
    quiet = build_payload(_trace(), [], None)
    assert quiet["assertion_expectation"]["status"] == "not-checked"
    assert quiet["status"] == "pass"

    loud = build_payload(_trace(events=[_event(0, "fail")]), [], None)
    assert loud["assertion_expectation"]["status"] == "not-checked"
    assert loud["status"] == "fail"
    assert "observed 1 assertion failure(s)" in loud["errors"]


def test_a_failure_summary_carries_named_fields_and_never_a_raw_payload() -> None:
    """The drawing says at most nine named fields and no buffer. The summary is built
    from a fixed list of keys, so a field nobody listed cannot ride along."""
    event = _event(7, "fail", stage="pixel", slot="t0", resource_id="rt0")
    event["assertion"] = "depth target still bound"
    event["raw_buffer"] = "0" * 64
    report = evaluate_assertions(_trace(events=[event]))
    summary = report["failures"][0]
    assert set(summary) <= {
        "seq", "frame_id", "pass_id", "stage", "slot",
        "resource_id", "assertion", "verdict", "provenance",
    }
    assert "raw_buffer" not in summary
    assert summary["seq"] == 7 and summary["verdict"] == "fail"


def test_every_string_in_the_summary_goes_through_the_redactor() -> None:
    """Nine redaction rules run over each string field. The drawing names five shapes,
    so five are driven here, one of them a path built at runtime."""
    token = "ghp_" + "a" * 24
    drive = "D:" + chr(92) + "captures" + chr(92) + "frame.rdc"
    shapes = (token, "AKIAIOSFODNN7EXAMPLE", "password: hunter2", drive, "/home/someone/x")
    event = _event(0, "fail")
    event["assertion"] = " ".join(shapes)
    report = evaluate_assertions(_trace(events=[event]))
    scrubbed = report["failures"][0]["assertion"]
    for shape in shapes:
        assert shape not in scrubbed, shape
    assert scrubbed.count("<redacted>") == len(shapes)


def test_nothing_longer_than_the_bound_survives_and_truncation_runs_last() -> None:
    """Two hundred and forty characters, and a secret at the tail is removed before
    the tail is thrown away, so the order the card claims is the order that runs."""
    assert MAX_FIELD_LENGTH == 240
    tail = "AKIAIOSFODNN7EXAMPLE"
    scrubbed = scrub_text("e" * (MAX_FIELD_LENGTH + 40) + " " + tail)
    assert tail not in scrubbed
    assert len(scrubbed) <= MAX_FIELD_LENGTH
    assert scrubbed.endswith("...")


def test_a_schema_error_is_named_with_its_path_and_scrubbed_before_printing(tmp_path, capsys) -> None:
    """Two claims in one row. The error carries the path that produced it, and the
    value that broke the rule is redacted out of the message reporting it."""
    drive = "D:" + chr(92) + "keys" + chr(92) + "id.pem"
    trace = _trace(source={"kind": drive, "path_or_handle": "x"})
    code, payload = _run(tmp_path, capsys, trace)
    assert code == 1
    errors = payload["schema_errors"]
    assert any(error.startswith("source/kind:") for error in errors)
    assert all("D:" not in error for error in errors)
    assert any("<redacted>" in error for error in errors)


def test_each_row_of_the_card_reports_a_status_the_tool_can_report(tmp_path, capsys) -> None:
    """The card promises eleven endings. Most are settled above one at a time; this
    reads the rows back off the spec and checks the shape of the table itself."""
    card = json.loads(_SPEC.read_text(encoding="utf-8"))["cards"][0]
    rows = card["fields"]
    assert len(rows) == 11
    assert [row["value"] for row in rows].count("ERROR") == 1
    assert sorted({row["value"] for row in rows}) == ["ERROR", "FAIL", "PASS"]
    assert [row.get("tone") for row in rows].count("drift") == 1

    code, payload = _run(tmp_path, capsys, _trace())
    assert code == 0 and payload["status"] == "pass"
    code, payload = _run(tmp_path, capsys, _trace(events=[_event(0, "fail")]))
    assert code == 1 and payload["status"] == "fail"
