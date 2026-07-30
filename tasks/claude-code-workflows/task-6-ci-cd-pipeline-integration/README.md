# Task Statement 3.6: Integrate Claude Code into CI/CD pipelines

## Knowledge of
- The -p (or --print) flag for running Claude Code in non-interactive mode in automated pipelines
- --output-format json and --json-schema CLI flags for enforcing structured output in CI contexts
- CLAUDE.md as the mechanism for providing project context (testing standards, fixture conventions, review criteria) to CI-invoked Claude Code
- Session context isolation: why the same Claude session that generated code is less effective at reviewing its own changes compared to an independent review instance

## Skills in
- Running Claude Code in CI with the -p flag to prevent interactive input hangs
- Using --output-format json with --json-schema to produce machine-parseable structured findings for automated posting as inline PR comments
- Including prior review findings in context when re-running reviews after new commits, instructing Claude to report only new or still-unaddressed issues to avoid duplicate comments
- Providing existing test files in context so test generation avoids suggesting duplicate scenarios already covered by the test suite
- Documenting testing standards, valuable test criteria, and available fixtures in CLAUDE.md to improve test generation quality and reduce low-value test output

---

# Subject

A small invoice/billing service (`billing/`) with a two-job CI pipeline
(`.github/workflows/claude-ci.yml`) that runs Claude Code headlessly against
every PR: one job reviews the diff, the other fills in missing test coverage.

- `claude-review` uses `-p`, `--output-format json`, and `--json-schema` to
  produce structured findings, and is told about `ci/prior-findings.json` so a
  re-run doesn't re-post a comment for something it already flagged.
- `claude-test-gen` uses `-p` with existing test files as context, so it adds
  coverage for `billing/tax.py` (which has none) without duplicating what
  `tests/test_discounts.py` and `tests/test_invoice.py` already cover.
- `billing/invoice.py` has a real, planted bug: `total_cents()`'s docstring
  claims it applies each line item's discount, but the implementation doesn't.
  Neither existing test file catches it — that gap is what the CI jobs below
  are supposed to close.

---

# How to verify

This task has no single script to run — it's a CI pipeline config plus the
codebase it operates on. Since this pipeline can't actually fire GitHub
Actions from here, verify it by running the exact commands
`.github/workflows/claude-ci.yml` runs, directly from this folder (the same
non-interactive invocation a CI runner would make).

```bash
cd tasks/claude-code-workflows/task-6-ci-cd-pipeline-integration
claude -p "Review this PR's diff against this repo's CLAUDE.md review criteria. \
ci/prior-findings.json lists issues already reported on an earlier run of this same PR — \
treat those as already known and set their status to still_open instead of reporting them again. \
Only give new findings a status of new. Treat every file under billing/ as the diff to review." \
  --output-format json \
  --json-schema "$(cat ci/review-findings-schema.json)"
```
Expected: a single JSON object whose `structured_output.findings` array validates against
`ci/review-findings-schema.json`. A real run found the planted `invoice.py` bug and correctly
marked it `"still_open"` (not `"new"`) because it's already in `ci/prior-findings.json` — it did
not re-report it as if it were freshly discovered. It also found genuinely new issues (unvalidated
input in `add_line_item`, and a rounding bug in `tax.py`/`discounts.py`), each marked `"new"`.

```bash
python ci/post_findings.py ci/review-findings.json
```
Expected: prints one `[inline comment]` line per `"new"` finding, and reports how many
`"still_open"` findings were skipped — this is the dedup behavior the review job depends on.

```bash
claude -p "Per this repo's CLAUDE.md testing standards, find any billing/ module with missing \
positive-case or edge-case coverage and write the missing tests. tests/ already has \
test_discounts.py and test_invoice.py — read them first and do not propose scenarios they \
already cover. Reuse tests/fixtures/sample_invoices.json rather than inventing new sample data." \
  --output-format json
```
Expected: a new `tests/test_tax.py` (the module with zero coverage), one added edge case in
`tests/test_discounts.py` (negative-percent, the one bound the existing suite didn't check), and
new discount-aware assertions in `tests/test_invoice.py` built from
`tests/fixtures/sample_invoices.json`. A real run did exactly this — and one of the new
`test_invoice.py` assertions genuinely fails, since it exercises the same planted `total_cents()`
bug the review job flagged. The run reported the failure rather than weakening the assertion to
match the broken behavior.

```bash
claude -p "Review this PR's diff against this repo's CLAUDE.md review criteria. Treat every file under billing/ as the diff to review." --output-format json --json-schema "$(cat ci/review-findings-schema.json)"
```
Expected: this and the test-gen run above each print a different `session_id` in their JSON
envelope. That's session isolation in practice — the review job's `-p` call is a brand-new,
stateless process every time. It never inherits the test-gen job's context, and it never inherits
whatever session (a developer's local Claude Code session, for instance) actually wrote the diff
being reviewed. A review run cannot rationalize past its own prior reasoning, because it has none.

---

# Implementation Info

> `.github/workflows/claude-ci.yml` is the CI pipeline: a `claude-review` job and a
> `claude-test-gen` job, each an independent `claude -p` invocation. `CLAUDE.md` is the project
> context both jobs read. `ci/` holds the schema, the prior-findings artifact, and the (illustrative)
> comment-posting script. `billing/` and `tests/` are the sample codebase both jobs operate on.

## How each Task Info item is covered:

- **The -p flag for non-interactive CI runs** — `.github/workflows/claude-ci.yml`

  ```yaml
  run: |
    claude -p "Review this PR's diff against this repo's CLAUDE.md review criteria. \
    ci/prior-findings.json lists issues already reported on an earlier run of this same PR — \
    treat those as already known and set their status to still_open instead of reporting them again. \
    Only give new findings a status of new." \
      --output-format json \
      --json-schema "$(cat ci/review-findings-schema.json)" \
      > ci/review-findings.json
  ```
  Both CI jobs invoke `claude -p` — never an interactive session — so a GitHub Actions runner with
  no TTY never hangs waiting for input.

- **--output-format json / --json-schema for structured CI output** — `ci/review-findings-schema.json`

  ```json
  {
    "type": "object",
    "properties": {
      "findings": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "file": {"type": "string"},
            "line": {"type": "integer"},
            "severity": {"type": "string", "enum": ["low", "medium", "high"]},
            "description": {"type": "string"},
            "status": {"type": "string", "enum": ["new", "still_open"]}
          },
          "required": ["file", "severity", "description", "status"]
        }
      }
    },
    "required": ["findings"]
  }
  ```
  The review job's `--json-schema` forces every finding into this shape, so `ci/post_findings.py`
  can parse `structured_output.findings` directly instead of scraping prose.

- **CLAUDE.md providing project context to CI-invoked Claude Code** — `CLAUDE.md`

  ```markdown
  ## Review criteria

  - Flag correctness bugs and security issues (e.g. unvalidated input reaching
    a money calculation, injection risks).
  - Do not flag style or formatting — a separate linter owns that, not code
    review.
  ```
  Neither `claude -p` invocation in the workflow passes review criteria or testing standards
  inline — both jobs pick this up automatically from `CLAUDE.md` because they run with this
  folder as their working directory.

- **Session context isolation** — `.github/workflows/claude-ci.yml`

  ```yaml
  jobs:
    claude-review:
      steps:
        - run: claude -p "..." --output-format json --json-schema "..." > ci/review-findings.json
    claude-test-gen:
      steps:
        - run: claude -p "..." --output-format json > ci/test-gen-output.json
  ```
  Each job is its own `claude -p` process. A live run of the review prompt and a live run of the
  test-gen prompt returned two different `session_id` values in their JSON output — neither job
  continues the other's session, and neither continues whatever session originally wrote the diff.
  That's what makes an independent review instance more reliable than asking the authoring session
  to grade its own work: it has no prior reasoning to anchor on.

- **Prior findings in context to avoid duplicate re-review comments** — `ci/prior-findings.json`

  ```json
  {
    "findings": [
      {
        "file": "billing/invoice.py",
        "line": 17,
        "severity": "high",
        "description": "total_cents() docstring says it applies each line's discount_percent, but it just returns subtotal_cents() — discounted invoices overcharge the customer.",
        "status": "new"
      }
    ]
  }
  ```
  The review job's prompt tells Claude to treat this file's entries as already known and mark them
  `still_open` rather than reporting them again. A live re-run did exactly that for this exact
  finding, while still surfacing genuinely new issues as `new`.

- **Existing test files in context to avoid duplicate test-gen scenarios** — `tests/test_discounts.py`

  ```python
  def test_full_discount():
      assert apply_percentage_discount(1000, 100) == 0


  def test_rejects_out_of_range():
      with pytest.raises(ValueError):
          apply_percentage_discount(1000, 150)
  ```
  The test-gen prompt points at this file and `tests/test_invoice.py` and says not to duplicate
  what they already cover. A live run left this file's existing scenarios untouched, added only the
  one missing bound (`test_rejects_negative_percent`), and wrote all-new coverage for
  `billing/tax.py`, which had no test file at all.

- **CLAUDE.md documenting testing standards and fixtures for test generation** — `CLAUDE.md`

  ```markdown
  ## Testing standards

  - Tests use `pytest`. One test file per module: `tests/test_<module>.py`.
  - Reuse `tests/fixtures/sample_invoices.json` for any test that needs invoice
    line-item data — don't invent new inline sample data.
  ```
  The test-gen job's real output built its new `total_cents()` assertions directly from
  `tests/fixtures/sample_invoices.json`'s `normal` and `fully_discounted_line` entries, per this
  convention, instead of inventing new sample invoices inline.
