# AGENTS.md

This repository is a public-safe Python package for validating renderer/GPU
trace fixtures and producing bounded, redacted receipts.

Rules:
- Do not commit `.env`, raw private traces, customer captures, or local
  generated artifacts.
- Keep fixture payloads synthetic and reviewable; redact absolute paths and
  credential-shaped strings in examples.
- Keep README, USAGE, schema behavior, package metadata, CI, and changelog
  aligned whenever validation output changes.
- Run `python -m pytest` before release.
- Treat reports as evidence summaries, not renderer certification.
