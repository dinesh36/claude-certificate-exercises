# CLAUDE.md

This is the **legacy CRM migration** sample project (Task Statement 3.5) — a small script that migrates customer records exported from a retired CRM into the JSON schema the new system's importer expects. It exists to demonstrate iterative refinement techniques: concrete input/output examples, test-driven iteration, the interview pattern, and batching interacting fixes vs. sequential independent ones.

This file is this sample project's own **project-level** config. It is nested inside the larger certification repo, so a live Claude Code session opened anywhere under here also inherits the outer repo's own root `CLAUDE.md` above this one.

## Project layout

- `spec/transform-spec.md` — the prose spec for the row transform, handed down from the migration's product owner. Deliberately underspecified in places — that's the starting point for this task, not a bug in the sample.
- `data/legacy_customers_sample.csv` — a small sample export from the legacy CRM, including the null, malformed, and duplicate rows the transform has to handle.
- `migration/migrate.py` — the transform implementation. Currently a first pass, written straight from the prose spec.
- `migration/test_migrate.py` — the test suite for the transform. Starts nearly empty; growing this file before touching `migrate.py` is the point of the TDD exercise in this task's README.

## Conventions

- Target schema: every migrated record is a JSON object with `customer_id` (str), `full_name` (str), `phone_e164` (str or null), `signup_date` (ISO-8601 str or null).
- A row that cannot be mapped into this shape is written to `data/rejects.jsonl` with a `reason` field — never silently dropped.
- Tests live in `migration/test_migrate.py` and run with `pytest`, from inside `migration/`.
