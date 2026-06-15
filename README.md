# gpu-trace-validator

`gpu-trace-validator` validates GPU trace JSON fixtures and prints a compact
summary of schema and assertion results. Report fields are redacted and bounded
so fixture output stays useful without echoing local paths or credential-shaped
values. It is built for graphics experiments that need inspectable frame or pass
receipts without a heavyweight trace database.

## Install

```bash
python -m pip install gpu-trace-validator
```

## Usage

```bash
gpu-trace-validator trace.json
gpu-trace-validator --schema schema/gpu_trace.schema.json --json trace.json
```

## Notes

- This CLI validates format and assertion summaries.
- It does not capture GPU work; it validates fixtures produced elsewhere.
- `--expect-failures` reports whether observed assertion failures matched the
  expected count.
- Reports are summaries, not certification or trust verdicts.
- JSON schema files are bundled with the package.
