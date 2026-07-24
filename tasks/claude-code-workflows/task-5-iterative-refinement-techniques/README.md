# Task Statement 3.5: Apply iterative refinement techniques for progressive improvement
## Knowledge of
- Concrete input/output examples as the most effective way to communicate expected transformations when prose descriptions are interpreted inconsistently
- Test-driven iteration: writing test suites first, then iterating by sharing test failures to guide progressive improvement
- The interview pattern: having Claude ask questions to surface considerations the developer may not have anticipated before implementing
- When to provide all issues in a single message (interacting problems) versus fixing them sequentially (independent problems)
## Skills in
- Providing 2–3 concrete input/output examples to clarify transformation requirements when natural language descriptions produce inconsistent results
- Writing test suites covering expected behavior, edge cases, and performance requirements before implementation, then iterating by sharing test failures
- Using the interview pattern to surface design considerations (e.g., cache invalidation strategies, failure modes) before implementing solutions in unfamiliar domains
- Providing specific test cases with example input and expected output to fix edge case handling (e.g., null values in migration scripts)
- Addressing multiple interacting issues in a single detailed message when fixes interact, versus sequential iteration for independent issues

---

# Subject
A legacy CRM data migration sample project: a script that transforms customer records exported from a retired CRM into the JSON schema a new system's importer expects. It demonstrates the iterative-refinement techniques a developer uses when collaborating with Claude on ambiguous, real-world code — not a static configuration mechanism.
- `spec/transform-spec.md` is deliberately underspecified in exactly the ways real handoff specs are: "normalize to a consistent format" without naming the format, "handle these cases sensibly" without naming the cases.
- `data/legacy_customers_sample.csv` carries the null, malformed, and duplicate rows the transform actually has to handle, so every technique below is exercised against real data instead of a hypothetical.
- `migration/migrate.py` and `migration/test_migrate.py` are a genuine first pass, not a finished implementation — the "How to verify" prompts below are what takes them from first pass to correct.

---

# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project). `migrate.py` only uses the standard library, and `pytest` is already resolved by the repo's root `uv` project — no extra install step is needed.
```bash
uv run tasks/claude-code-workflows/task-5-iterative-refinement-techniques/migration/migrate.py
```
Prints the current migrated JSON for every row in `data/legacy_customers_sample.csv`.
```bash
uv run pytest tasks/claude-code-workflows/task-5-iterative-refinement-techniques/migration/test_migrate.py -q
```
Runs the seed test suite in `migration/test_migrate.py`.

---

# How to verify
Running the script confirms the current state, but the point of this task is the interactive refinement session, not the script's output alone. Open a Claude Code session with this folder (`tasks/claude-code-workflows/task-5-iterative-refinement-techniques/`) as the working directory, then try the prompts below in order (each builds on the previous one's result).

```
Implement parse_date in migration/migrate.py to satisfy spec/transform-spec.md's
"Parse the signup date into a consistent format" — decide the target format yourself.
```
Expected: because the spec never pins down the exact shape, Claude's first answer may leave already-ISO-looking dates like `"2023-04-11"` alone but handle `data/legacy_customers_sample.csv`'s `"05/02/2023"` row (a different source format than the rest) and the empty-string row inconsistently — e.g. reformatting one but not the other, or guessing at whether an empty string should become `null` or stay `""`. This is the inconsistent-interpretation problem the next prompt fixes.

```
Here's the exact transform I need — 3 examples:
"2023-04-11" -> "2023-04-11"
"05/02/2023" -> "2023-05-02"
""           -> null
Redo parse_date to match these exactly.
```
Expected: the output now normalizes every date to `YYYY-MM-DD` regardless of source format, and maps an empty string to `null` instead of leaving it as `""` — a case the prose spec never mentioned at all. Compare this run's determinism against the previous prompt's guesswork; that gap is the concrete-example technique.

```
Before touching parse_date, add tests to migration/test_migrate.py covering:
a row with signup="", a row with signup="05/02/2023" (a different format than the rest),
and a row with signup="2023-04-11" (the common format, should stay unchanged).
Run pytest, show me the failures, then iterate on migrate.py until they pass.
```
Expected: Claude writes the tests first, runs `pytest` from `migration/` — the seed test (`parse_date("") is None`) already fails against the current passthrough implementation, and the `"05/02/2023"` case fails too — shows the real failures, then edits `migrate.py` and reruns until green. A visible write-test, see-it-fail, fix, rerun loop, not a one-shot guess at the fix. (The `"2023-04-11"` case should already pass — a useful regression check alongside the two real failures.)

```
Two rows in data/legacy_customers_sample.csv share customer_id C-1001 but came from
different export batches. Add logic to migrate.py to merge them into one record.
```
Expected: before writing code, Claude asks clarifying questions — e.g. which row wins on conflicting fields, whether the most recent `signup_date` should win, whether a merge should be logged, what happens with a third duplicate later — instead of silently picking a merge strategy. This is the interview pattern applied to an underspecified design decision, not the cache-invalidation example the task statement itself uses, but the same shape of problem.

```
Three things are wrong right now:
1. migrate() never writes unmappable rows (e.g. the phone="not-a-phone" row) to
   data/rejects.jsonl, even though CLAUDE.md's convention requires it.
2. parse_date doesn't normalize "05/02/2023"-style dates to YYYY-MM-DD, so C-1002's
   signup_date is inconsistent with every other row.
3. Because of #2, the merge logic from before can't reliably tell which of two duplicate
   rows has the more recent signup_date when they're in different formats.
Fix these.
```
Expected: Claude should treat #2 and #3 together in one pass — the merge logic's recency tie-break can't be fixed correctly without fixing the date-format bug it depends on — while calling out #1 (the missing reject-file routing) as unrelated and fixing it independently, rather than either bundling all three blindly or fixing all three in isolated edits that don't cross-check against each other.

---

# Implementation Info
> A legacy-CRM-to-JSON migration sample: `spec/transform-spec.md` (deliberately ambiguous prose spec), `data/legacy_customers_sample.csv` (null/malformed/duplicate rows), `migration/migrate.py` + `migration/test_migrate.py` (a genuine first-pass implementation and seed test suite), and `README.md`'s "How to verify" section (the documented prompts that exercise each technique in a live session).
## How each Task Info item is covered:
- **Concrete input/output examples as the most effective way to communicate expected transformations when prose descriptions are interpreted inconsistently** — `spec/transform-spec.md`

  ```markdown
  - `signup` -> `signup_date`. Parse the signup date into a consistent format.
  ```

  This line never names an actual target format, which is exactly the condition under which prose is interpreted inconsistently — the first "How to verify" prompt pair demonstrates the fix, using the mixed `"2023-04-11"` / `"05/02/2023"` formats already present in `data/legacy_customers_sample.csv`.

- **Test-driven iteration: writing test suites first, then iterating by sharing test failures to guide progressive improvement** — `migration/test_migrate.py`

  ```python
  def test_parse_date_returns_null_for_empty_string():
      assert parse_date("") is None
  ```

  This seed test already fails against the starter `migrate.py` (`parse_date` currently passes `""` straight through instead of returning `None`), so a reader who runs `pytest` before writing more tests immediately sees a real failure to iterate against, not a hypothetical one.

- **The interview pattern: having Claude ask questions to surface considerations the developer may not have anticipated before implementing** — `README.md` ("How to verify", the duplicate-merge prompt)

  ```
  Two rows in data/legacy_customers_sample.csv share customer_id C-1001 but came from
  different export batches. Add logic to migrate.py to merge them into one record.
  ```

  The prompt withholds the merge strategy on purpose, so the correct response surfaces clarifying questions (conflict resolution, recency, logging) before any code is written.

- **When to provide all issues in a single message (interacting problems) versus fixing them sequentially (independent problems)** — `README.md` ("How to verify", the three-bugs prompt)

  ```
  2. parse_date doesn't normalize "05/02/2023"-style dates to YYYY-MM-DD, so C-1002's
     signup_date is inconsistent with every other row.
  3. Because of #2, the merge logic from before can't reliably tell which of two duplicate
     rows has the more recent signup_date when they're in different formats.
  ```

  Bugs #2 and #3 are stated as causally dependent in the same message on purpose, while #1 (the missing reject-file routing) is unrelated — the correct response treats them differently instead of applying one uniform strategy to all three.

- **Providing 2–3 concrete input/output examples to clarify transformation requirements when natural language descriptions produce inconsistent results** — `README.md` ("How to verify", second prompt)

  ```
  "2023-04-11" -> "2023-04-11"
  "05/02/2023" -> "2023-05-02"
  ""           -> null
  ```

  Exactly 3 examples, chosen to each pin down a different ambiguity left open by the prose spec: leaving an already-conformant date unchanged, reformatting a differently-shaped source date, and the empty-string case.

- **Writing test suites covering expected behavior, edge cases, and performance requirements before implementation, then iterating by sharing test failures** — `README.md` ("How to verify", TDD prompt)

  ```
  Before touching parse_date, add tests to migration/test_migrate.py covering:
  a row with signup="", a row with signup="05/02/2023" (a different format than the rest),
  and a row with signup="2023-04-11" (the common format, should stay unchanged).
  ```

  Names three concrete edge cases up front and asks for tests before implementation, then explicitly asks for the failures to be shown before `migrate.py` is edited — the write-test, see-it-fail, fix loop rather than fix-and-hope.

- **Using the interview pattern to surface design considerations (e.g., cache invalidation strategies, failure modes) before implementing solutions in unfamiliar domains** — `README.md` ("How to verify", same duplicate-merge prompt as above)

  The task statement's own worked example is cache invalidation; this sample's equivalent unfamiliar-domain design gap is merge-conflict strategy for duplicate customer records — structurally the same kind of decision a developer shouldn't let Claude guess at silently.

- **Providing specific test cases with example input and expected output to fix edge case handling (e.g., null values in migration scripts)** — `data/legacy_customers_sample.csv`, `migration/migrate.py`

  ```csv
  C-1002,Tomas Reyes,415.555.9981,05/02/2023
  C-1005,Mateo Alvarez,not-a-phone,
  ```

  Row `C-1002` carries a differently-formatted signup date, row `C-1005` has a null signup — real rows the TDD prompt's named edge cases (`signup=""`, `signup="05/02/2023"`, `signup="2023-04-11"`) map directly onto, mirroring the task statement's own null-values-in-migration-scripts example.

- **Addressing multiple interacting issues in a single detailed message when fixes interact, versus sequential iteration for independent issues** — `README.md` ("How to verify", same three-bugs prompt as above)

  All three bugs are given in one message, but only two of them actually interact — the point of the exercise is choosing to treat #2/#3 as one fix and #1 as a separate one, not deciding message count in advance.
