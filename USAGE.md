# Usage Guide

`gpu-trace-validator` validates a GPU trace JSON fixture against a bundled JSON
Schema and emits a bounded, redacted summary ("receipt") of the schema check and
the assertion events found in the trace.

It does **not** capture GPU work. It validates fixtures produced elsewhere.

## Install

```bash
python -m pip install gpu-trace-validator
```

Requires Python 3.10+. The only runtime dependency is `jsonschema>=4.22`.

## Command-line interface

```
gpu-trace-validator [--schema PATH] [--expect-failures N] [--json] TRACE
```

| Argument / flag       | Meaning                                                                 |
| --------------------- | ----------------------------------------------------------------------- |
| `TRACE`               | Path to the GPU trace JSON file (required, positional).                 |
| `--schema PATH`       | Override the bundled schema with your own. Defaults to the packaged schema. |
| `--expect-failures N` | Assert that exactly `N` assertion events have `verdict: "fail"`.        |
| `--json`              | Print the full report as indented, key-sorted JSON instead of text.     |

Exit code is `0` when the overall status is `pass` and `1` when it is `fail`.

The schema ships inside the package, so you normally do not pass `--schema`.

### Status rules

- The report `status` is `fail` if there are any schema errors, or if
  `--expect-failures` is omitted and at least one assertion failed, or if
  `--expect-failures N` is given and the observed failure count is not `N`.
- With `--expect-failures N`, a trace whose failures match `N` reports `pass`
  even though individual assertions failed — this is how you encode
  "these failures are expected".

### Redaction

String fields in the report are scrubbed before printing: private keys, AWS
access key IDs, GitHub/OpenAI-style tokens, `bearer/token/api-key/password/secret`
assignments, Windows drive paths, and common Unix absolute paths are replaced
with `<redacted>`. Fields are also collapsed and truncated to 240 characters.

---

## Examples

> Expected output below was produced by running the commands against the
> repository's bundled fixtures in `tests/fixtures/`.

### 1. Validate a passing trace (text output)

```bash
gpu-trace-validator tests/fixtures/trace_pass.json
```

Expected output (exit code `0`):

```
gpu_trace_validation: pass
trace_id: trace-ok
assertions: 1 total, 0 fail, 0 unknown
```

### 2. Validate a failing trace (default expectations)

```bash
gpu-trace-validator tests/fixtures/trace_fail.json
```

Expected output (exit code `1`):

```
gpu_trace_validation: fail
trace_id: trace-bad
assertions: 2 total, 2 fail, 0 unknown
error: observed 2 assertion failure(s)
```

### 3. Encode expected failures (text output)

The fail fixture has exactly two failing assertions. Declaring that they are
expected flips the overall status back to `pass`:

```bash
gpu-trace-validator --expect-failures 2 tests/fixtures/trace_fail.json
```

Expected output (exit code `0`):

```
gpu_trace_validation: pass
trace_id: trace-bad
assertions: 2 total, 2 fail, 0 unknown
```

If the observed count does not match (e.g. `--expect-failures 1` against the
same fixture), the status is `fail` and the report lists:
`expected 1 assertion failure(s), observed 2`.

### 4. Full JSON report

```bash
gpu-trace-validator --expect-failures 2 --json tests/fixtures/trace_fail.json
```

Expected output (exit code `0`, abridged):

```json
{
  "assertion_expectation": {
    "expected_failures": 2,
    "observed_failures": 2,
    "status": "pass"
  },
  "assertions": {
    "assertion_count": 2,
    "failure_count": 2,
    "failures": [
      {
        "assertion": "frame_count",
        "frame_id": 1,
        "pass_id": "p1",
        "provenance": "gpu",
        "resource_id": "r1",
        "seq": 1,
        "slot": "0",
        "stage": "decode",
        "verdict": "fail"
      }
    ],
    "status": "fail",
    "unknown_count": 0,
    "unknowns": []
  },
  "errors": [],
  "schema_errors": [],
  "status": "pass",
  "trace_id": "trace-bad"
}
```

(The second failure entry is omitted above for brevity; the real output
includes both.)

---

## Python API

The validation primitives are importable from `gpu_trace_validator.validator`:

```python
from pathlib import Path

from gpu_trace_validator.validator import (
    DEFAULT_SCHEMA,      # Path to the bundled JSON Schema
    load_json,           # load_json(path) -> Any
    load_trace,          # load_trace(path) -> dict  (root must be an object)
    evaluate_assertions, # evaluate_assertions(trace) -> assertion summary dict
    build_payload,       # build_payload(trace, schema_errors, expected_failures) -> report dict
)

trace = load_trace(Path("tests/fixtures/trace_fail.json"))

# Summarize assertion events.
summary = evaluate_assertions(trace)
print(summary["status"], summary["failure_count"])  # -> fail 2

# Build the full redacted report. Pass [] when you have no schema errors,
# and an expected-failure count (or None to skip that check).
report = build_payload(trace, [], expected_failures=2)
print(report["status"])                               # -> pass
print(report["assertion_expectation"]["status"])      # -> pass
```

`build_payload` does not run schema validation itself; pass a list of schema
error strings (the CLI builds these with `jsonschema.Draft202012Validator`).
`DEFAULT_SCHEMA` is the path to the packaged schema if you want to validate
yourself:

```python
from jsonschema import Draft202012Validator
from gpu_trace_validator.validator import load_json, DEFAULT_SCHEMA

schema = load_json(DEFAULT_SCHEMA)
errors = [e.message for e in Draft202012Validator(schema).iter_errors(trace)]
report = build_payload(trace, errors, expected_failures=2)
```
