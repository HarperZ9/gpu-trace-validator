# Changelog

## 0.2.0 (unreleased)

- From v0.2.0, code is licensed FSL-1.1-MIT. Earlier releases remain under MIT.
- `LICENSE` is the FSL-1.1-MIT text from fsl.software, with licensor Zain Dana Harper and copyright 2026.
- `pyproject.toml` declares `license = "FSL-1.1-MIT"` (PEP 639, hatchling 1.27 or later) and drops the MIT classifier; PyPI has no FSL classifier. Version 0.2.0 in `pyproject.toml` and `__version__`.
- Documents GitHub tag and source-checkout install paths while PyPI has no
  `gpu-trace-validator` project.
- Refreshes public/developer delivery with repo-local agent instructions,
  current GitHub Actions majors, and ASCII-safe public documentation.
- Redacts credential-shaped strings and absolute local paths from validation
  payload fields.
- Updates bundled trace fixtures so they satisfy the packaged schema.
- Adds regression coverage for schema-valid fixtures and report redaction.

## 0.1.0 - 2026-06-13

- Initial public release candidate.
- Ships GPU trace JSON schema validation, compact assertion summaries, CLI
  behavior, and regression fixtures.
- Adds Python package metadata, CI, license, authorship, and contribution
  boundary files.
