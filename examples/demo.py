#!/usr/bin/env python3
# Best-effort demo — not runtime-verified by author.
"""End-to-end demo of gpu-trace-validator.

Exercises the public Python API and the CLI entry point against the bundled
test fixtures. Run from the repository root:

    PYTHONPATH=src python examples/demo.py

or, once the package is installed:

    python examples/demo.py
"""

from __future__ import annotations

from pathlib import Path

from gpu_trace_validator.cli import main
from gpu_trace_validator.validator import (
    DEFAULT_SCHEMA,
    build_payload,
    evaluate_assertions,
    load_json,
    load_trace,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"


def api_demo() -> None:
    print("=== Python API ===")
    print(f"bundled schema: {DEFAULT_SCHEMA.name} (exists={DEFAULT_SCHEMA.exists()})")

    # Passing trace: no schema errors, no assertion failures.
    ok = load_trace(FIXTURES / "trace_pass.json")
    ok_summary = evaluate_assertions(ok)
    print(
        f"trace_pass : status={ok_summary['status']} "
        f"assertions={ok_summary['assertion_count']} "
        f"failures={ok_summary['failure_count']}"
    )

    # Failing trace: two failing assertions.
    bad = load_trace(FIXTURES / "trace_fail.json")
    bad_summary = evaluate_assertions(bad)
    print(
        f"trace_fail : status={bad_summary['status']} "
        f"assertions={bad_summary['assertion_count']} "
        f"failures={bad_summary['failure_count']}"
    )

    # Build the full report. Declaring the two failures as expected -> pass.
    expected = build_payload(bad, [], expected_failures=2)
    print(f"trace_fail with --expect-failures 2 -> report status={expected['status']}")

    # Mismatched expectation -> fail, with an explanatory error.
    mismatch = build_payload(bad, [], expected_failures=1)
    print(
        f"trace_fail with --expect-failures 1 -> report status={mismatch['status']} "
        f"errors={mismatch['errors']}"
    )

    # Validate yourself with the bundled schema (optional dependency: jsonschema).
    schema = load_json(DEFAULT_SCHEMA)
    print(f"loaded schema title: {schema.get('title')!r}")


def cli_demo() -> None:
    print("\n=== CLI (gpu_trace_validator.cli.main) ===")
    pass_path = str(FIXTURES / "trace_pass.json")
    fail_path = str(FIXTURES / "trace_fail.json")

    print("\n$ gpu-trace-validator trace_pass.json")
    code = main([pass_path])
    print(f"[exit={code}]")

    print("\n$ gpu-trace-validator trace_fail.json")
    code = main([fail_path])
    print(f"[exit={code}]")

    print("\n$ gpu-trace-validator --expect-failures 2 trace_fail.json")
    code = main(["--expect-failures", "2", fail_path])
    print(f"[exit={code}]")

    print("\n$ gpu-trace-validator --json trace_pass.json")
    code = main(["--json", pass_path])
    print(f"[exit={code}]")


if __name__ == "__main__":
    api_demo()
    cli_demo()
