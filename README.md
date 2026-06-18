# GPU Trace Validator

> Validate GPU trace JSON against a schema; emit bounded, redacted receipts.

[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![version](https://img.shields.io/badge/version-0.1.0-informational.svg)
[![CI](https://github.com/HarperZ9/gpu-trace-validator/actions/workflows/ci.yml/badge.svg)](https://github.com/HarperZ9/gpu-trace-validator/actions/workflows/ci.yml)
[![part of: AI-accountability toolkit](https://img.shields.io/badge/part_of-AI--accountability_toolkit-7a5cff.svg)](https://harperz9.github.io)

## Install

```bash
python -m pip install gpu-trace-validator
```

## Usage

```bash
gpu-trace-validator trace.json
gpu-trace-validator --expect-failures 0 --json trace.json
```

The JSON Schema ships inside the package and is used by default, so `--schema`
is only needed to override it with your own file. See [USAGE.md](USAGE.md) for
worked examples, expected output, and the importable Python API.

## Notes

- This CLI validates format and assertion summaries.
- It does not capture GPU work; it validates fixtures produced elsewhere.
- `--expect-failures` reports whether observed assertion failures matched the
  expected count.
- Reports are summaries, not certification or trust verdicts.
- JSON schema files are bundled with the package.

---
**Zain Dana Harper** — small tools with explicit edges.
[Portfolio](https://harperz9.github.io) · [HarperZ9](https://github.com/HarperZ9)
<sub>Built with Claude Code; reviewed, tested, and owned by me.</sub>
