# CLAUDE.md

Project-level context for `billing`, a small invoice service. Both CI jobs in
`.github/workflows/claude-ci.yml` invoke Claude Code headlessly against this
repo, and this file is the only context they get beyond the diff itself.

## Testing standards

- Tests use `pytest`. One test file per module: `tests/test_<module>.py`.
- Reuse `tests/fixtures/sample_invoices.json` for any test that needs invoice
  line-item data — don't invent new inline sample data.
- Every public function needs a positive-case test and an edge-case test
  (zero, negative, or empty input). A function with only a positive-case test
  counts as missing coverage.

## Fixture conventions

- `tests/fixtures/sample_invoices.json` is the canonical fixture set. It has
  three invoices: a normal one, one with a 100%-discount line item, and one
  with a zero-quantity line item.
- Don't add a second fixtures file for the same kind of data — extend the
  existing one instead.

## Review criteria

- Flag correctness bugs and security issues (e.g. unvalidated input reaching
  a money calculation, injection risks).
- Do not flag style or formatting — a separate linter owns that, not code
  review.
- Money is rounded to the nearest cent. A change that produces an
  off-by-a-cent total is in scope.
