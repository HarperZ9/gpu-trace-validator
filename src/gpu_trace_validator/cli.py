from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .validator import DEFAULT_SCHEMA, build_payload, load_json, load_trace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a GPU trace fixture.")
    parser.add_argument("trace", help="Path to GPU trace JSON")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA), help="Path to GPU trace schema")
    parser.add_argument("--expect-failures", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    schema = load_json(args.schema)
    trace = load_trace(args.trace)
    schema_errors = []
    try:
        from jsonschema import Draft202012Validator

        validator = Draft202012Validator(schema)
        schema_errors = [
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in sorted(validator.iter_errors(trace), key=lambda item: list(item.path))
        ]
    except Exception as error:
        schema_errors = [str(error)]

    payload = build_payload(trace, schema_errors, args.expect_failures)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"gpu_trace_validation: {payload['status']}")
        print(f"trace_id: {payload['trace_id']}")
        asserts = payload['assertions']
        print(f"assertions: {asserts['assertion_count']} total, {asserts['failure_count']} fail, {asserts['unknown_count']} unknown")
        for error in payload['errors']:
            print(f"error: {error}")
    return 1 if payload['status'] == 'fail' else 0


if __name__ == "__main__":
    raise SystemExit(main())