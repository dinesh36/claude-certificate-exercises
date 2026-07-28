# Task Statement 4.1: Design prompts with explicit criteria to improve precision and reduce false positives
## Knowledge of
- The importance of explicit criteria over vague instructions (e.g., "flag comments only when claimed behavior contradicts actual code behavior" vs "check that comments are accurate")
- How general instructions like "be conservative" or "only report high-confidence findings" fail to improve precision compared to specific categorical criteria
- The impact of false positive rates on developer trust: high false positive categories undermine confidence in accurate categories
## Skills in
- Writing specific review criteria that define which issues to report (bugs, security) versus skip (minor style, local patterns) rather than relying on confidence-based filtering
- Temporarily disabling high false-positive categories to restore developer trust while improving prompts for those categories
- Defining explicit severity criteria with concrete code examples for each severity level to achieve consistent classification

---

# Subject
A code-review prompt is pointed at a small patient-intake validator module from a hospital's Python backend.

The module has three real issues (a docstring that lies about redacting PII before logging, a validation check that contradicts its own error message, and a SQL-injection bug) plus two plausible-looking non-issues (a stylistic list comprehension, and an intentional `RETRY_` naming convention).

- The same code is reviewed under three prompts of increasing specificity, and each run is checked against the fixed set of real issues and non-issues.

---

# How to verify
This task has no script to run. Open a **Claude Code** session at the repository root and paste the three prompts below yourself — each one asks Claude Code to read [intake_validator.py](intake_validator.py) by its relative path, so it needs file access. This won't work pasted into claude.ai's chat, which can't resolve a local repo path; if you want to test there instead, open the file yourself and paste its contents in place of the "Read ..." instruction. Paste each prompt into a **separate, fresh conversation** so later prompts aren't influenced by earlier answers.

Model output is non-deterministic, and the vague prompt's failure mode varies by run — sometimes it over-flags the style/naming lures, sometimes it under-covers by scoping itself too narrowly. The v1-to-v2 transition (disabling the `local_pattern` category) is the reliable part: it should consistently remove that specific false positive while keeping every true positive. That transition, not "does the vague prompt fail," is the actual mechanism the task statement is about.

### 1. Vague prompt (the anti-pattern)
```
You are a code reviewer. Read tasks/prompt-engineering/task-1-explicit-criteria-precision/intake_validator.py and check that its comments are accurate. Be conservative and only report high-confidence findings.
```
Look for: this prompt has two ways to fail, and a live run can show either. It may over-flag the style nit or the `RETRY_` naming convention, since "be conservative" names no concrete category to anchor on. Or — as happened in a recorded run — it may under-cover: it can read "check that comments are accurate" as scoping the whole review to comment accuracy, catch the docstring/MRN issues, and explicitly declare the SQL injection "outside scope" even though it noticed it. Neither failure is guaranteed on every run; both are absent once the categorical criteria in prompts 2 and 3 name `security` as a reportable category outright.

### 2. Explicit-criteria prompt v1 (`local_pattern` still reportable)
```
You are a code reviewer for a healthcare intake system. Read tasks/prompt-engineering/task-1-explicit-criteria-precision/intake_validator.py and report a finding only if it falls into one of these categories:
- comment_behavior_mismatch: a docstring/comment makes a factual claim about behavior, and the code contradicts it.
- bug: the code's logic is internally inconsistent or wrong (e.g. a check that contradicts its own error message).
- security: an exploitable vulnerability (e.g. SQL injection, logging sensitive data).
- local_pattern: a naming or structural choice that looks like a convention violation.

Do NOT report minor style preferences (e.g. list comprehension vs loop) unless they cause a bug or vulnerability.

For each finding output one line: `<severity> | <function> | <category> | <description>`. severity is one of:
- critical: exploitable now, e.g. unsanitized input reaching a database query.
- high: incorrect behavior with real user-facing or compliance impact, e.g. logging PII against a stated privacy claim.
- medium: incorrect behavior with limited or edge-case impact.
- low: anything below medium.
```
Look for: all 3 true positives, each on its own `severity | function | category | description` line, correctly classified (critical for the SQL injection, high for the redaction mismatch, medium for the MRN check) — plus, in a live run of this exact prompt, a `local_pattern` finding on `RETRY_store_intake`'s naming. That's the false positive v2 is designed to remove.

### 3. Explicit-criteria prompt v2 (`local_pattern` disabled)
```
You are a code reviewer for a healthcare intake system. Read tasks/prompt-engineering/task-1-explicit-criteria-precision/intake_validator.py and report a finding only if it falls into one of these categories:
- comment_behavior_mismatch: a docstring/comment makes a factual claim about behavior, and the code contradicts it.
- bug: the code's logic is internally inconsistent or wrong (e.g. a check that contradicts its own error message).
- security: an exploitable vulnerability (e.g. SQL injection, logging sensitive data).

Do NOT report:
- minor style preferences (e.g. list comprehension vs loop) unless they cause a bug or vulnerability.
- local naming/organizational patterns that are unconventional but consistent and intentional within this codebase (e.g. a prefix used consistently to mark a category of function) — local_pattern findings are temporarily disabled pending a follow-up pass on this specific category's prompt wording.

For each finding output one line: `<severity> | <function> | <category> | <description>`. severity is one of:
- critical: exploitable now, e.g. unsanitized input reaching a database query.
- high: incorrect behavior with real user-facing or compliance impact, e.g. logging PII against a stated privacy claim.
- medium: incorrect behavior with limited or edge-case impact.
- low: anything below medium.
```
Look for: the same 3 true positives, same severities — and this time no `local_pattern`/naming complaint about `RETRY_store_intake`, since that category is now explicitly excluded rather than left to the model's judgment.

### Checklist
True positives every prompt should catch:
- **comment-mismatch-redaction** (high) — `validate_intake`'s docstring claims SSN/DOB are redacted before logging, but `logger.warning` logs the raw form dict.
- **bug-mrn-length** (medium) — the error message says "8-digit" but the check enforces `len(mrn) != 7`.
- **security-sql-injection** (critical) — `store_intake` builds its SQL `INSERT` with an f-string.

False-positive lures a precise reviewer should skip:
- **style-list-comprehension** — `_summarize_errors`'s list comprehension is a style choice, not a bug.
- **local-pattern-retry-prefix** — `RETRY_store_intake`'s naming is an intentional, documented convention.

A live run of this exact task (recorded during scaffolding) produced 2/3 true positives and 0/2 false positives on the vague prompt — it caught the comment mismatch and the MRN bug, but explicitly scoped the SQL injection as "outside scope" of a comment-accuracy check — then 3/3 true positives and 1/2 false positives (`local-pattern-retry-prefix`) on v1, and 3/3 true positives and 0/2 false positives on v2. The categorical `security` criterion in prompts 2 and 3 is what guarantees the SQL injection can't be scoped away, and the v1→v2 transition is what removes the one remaining false positive.

---

# Implementation Info
> `intake_validator.py` is the real reviewed file. `README.md`'s "How to verify" section holds the three prompts a reader runs themselves, each pointing Claude Code at `intake_validator.py` by path, plus a Checklist of the ground-truth findings to compare against.
## How each Task Info item is covered:
- **Explicit criteria over vague instructions** — `README.md`

  ```
  You are a code reviewer. Read ... and check that its comments are accurate.
  Be conservative and only report high-confidence findings.
  ```

  Prompt 1 uses the task statement's own illustrative vague phrasing verbatim, while prompt 2 replaces it with named categories (`comment_behavior_mismatch`, `bug`, `security`, `local_pattern`) and an explicit skip list — both are run against identical code so the difference in specificity is the only variable.

- **"Be conservative" / "high-confidence only" failing to improve precision** — `README.md`

  ```
  You are a code reviewer. Read ... and check that its comments are accurate.
  Be conservative and only report high-confidence findings.
  ```

  Neither phrase defines what "conservative" or "high-confidence" means for a specific issue category, so the model has nothing categorical to anchor on. Prompt 2's own findings confirm the point from the other direction: it already names categories, and a live run still over-flagged `local_pattern`, because that one category's criterion was still too broad — precision comes from fixing the categorical definition, not from adding more conservative-sounding adjectives.

- **False positive impact on developer trust** — `README.md`

  ```
  local-pattern-retry-prefix — RETRY_store_intake's naming is an intentional,
  documented convention.
  ```

  A recorded live run showed prompt 2 catching all 3 true positives but also raising this 1 false positive; prompt 3 caught the same 3 true positives with 0 false positives. Dropping one noisy category to zero, without touching the categories that were already accurate, is the concrete version of "high false positive categories undermine confidence in accurate categories."

- **Writing specific criteria for report vs skip categories** — `README.md`

  ```
  - comment_behavior_mismatch: a docstring/comment makes a factual claim about
    behavior, and the code contradicts it.
  - bug: the code's logic is internally inconsistent or wrong ...
  - security: an exploitable vulnerability ...
  - local_pattern: a naming or structural choice that looks like a convention violation.

  Do NOT report minor style preferences (e.g. list comprehension vs loop) unless
  they cause a bug or vulnerability.
  ```

  Prompt 2 names the reportable categories (bugs, security, comment mismatches) and explicitly excludes minor style, matching the task statement's own "bugs, security ... versus ... minor style, local patterns" split.

- **Temporarily disabling a high false-positive category** — `README.md`

  ```
  Do NOT report:
  - minor style preferences (e.g. list comprehension vs loop) unless they cause a
    bug or vulnerability.
  - local naming/organizational patterns that are unconventional but consistent
    and intentional within this codebase ... — local_pattern findings are
    temporarily disabled pending a follow-up pass on this specific category's
    prompt wording.
  ```

  `local_pattern` moves from prompt 2's reportable list to prompt 3's skip list — the same category, disabled rather than deleted, with the prompt text itself noting it's pending a follow-up fix rather than a permanent removal.

- **Explicit severity criteria with concrete examples per level** — `README.md`

  ```
  severity is one of:
  - critical: exploitable now, e.g. unsanitized input reaching a database query.
  - high: incorrect behavior with real user-facing or compliance impact, e.g.
    logging PII against a stated privacy claim.
  - medium: incorrect behavior with limited or edge-case impact.
  - low: anything below medium.
  ```

  Each severity level pairs its abstract definition with a concrete example drawn from this exact codebase (the SQL injection for critical, the PII-logging mismatch for high), which is why both prompt 2 and prompt 3 runs classified the SQL injection as `critical` and the redaction mismatch as `high` consistently.
