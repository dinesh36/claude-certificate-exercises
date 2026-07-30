# Task Statement 4.4: Implement validation, retry, and feedback loops for extraction quality
## Knowledge of
- Retry-with-error-feedback: appending specific validation errors to the prompt on retry to guide the model toward correction
- The limits of retry: retries are ineffective when the required information is simply absent from the source document (vs format or structural errors)
- Feedback loop design: tracking which code constructs trigger findings (detected_pattern field) to enable systematic analysis of dismissal patterns
- The difference between semantic validation errors (values don't sum, wrong field placement) and schema syntax errors (eliminated by tool use)
## Skills in
- Implementing follow-up requests that include the original document, the failed extraction, and specific validation errors for model self-correction
- Identifying when retries will be ineffective (e.g., information exists only in an external document not provided) versus when they will succeed (format mismatches, structural output errors)
- Adding detected_pattern fields to structured findings to enable analysis of false positive patterns when developers dismiss findings
- Designing self-correction validation flows: extracting "calculated_total" alongside "stated_total" to flag discrepancies, adding "conflict_detected" booleans for inconsistent source data

---

# Subject
A monthly bank statement gets run through an extraction pipeline that pulls out transactions, reconciles totals, and flags data-quality issues.

The statement is built with three deliberate problems:
- A duplicated line item that makes the sum of transactions disagree with the printed ending balance by an exact, traceable amount.
- A transaction dated after the statement's own stated period.
- A referenced wire confirmation number that never actually appears anywhere in the document.

The prompts walk through an initial extraction, a retry driven by specific validation errors, and a check for the one issue retrying can't fix.

---

# How to verify
This task has no script to run. Open a **Claude Code** session at the repository root (the prompts below ask it to read a file by path, so it needs file access — this won't work pasted into claude.ai's chat, which can't resolve a local path).

Run all three prompts in the same conversation, in order — this is a multi-turn retry loop, not three independent tries.

### 1. Initial extraction
```
Read tasks/prompt-engineering/task-4-validation-retry-feedback-loops/bank_statement_march_2024.txt

Extract a JSON object with:
- transactions: array of {date, description, amount, detected_pattern (null unless something about this line looks off, e.g. "possible_duplicate_charge", "date_outside_statement_period"), conflict_detected (boolean, true if this line contradicts another part of the statement)}
- calculated_total: the ending balance you get by adding every transaction in the statement period to the beginning balance
- stated_total: the ending balance printed on the statement
- wire_confirmation_number: the confirmation number for the wire transfer out, if present in the document

Return only the JSON.
```
First-pass extractions vary, but commonly under-deliver in at least one of three ways: `calculated_total` is computed but never actually compared to `stated_total` (no discrepancy called out), the 04/02 transaction isn't flagged as being outside the stated March 1-31 period, or `wire_confirmation_number` gets a fabricated-looking value (e.g. a placeholder or an invented number) instead of `null` — because the statement never provides one.

### 2. Retry with specific validation errors
```
Your extraction has three problems:
1. calculated_total and stated_total don't reconcile — they're off by exactly $32.50. Figure out why and set conflict_detected accordingly on the line(s) responsible.
2. One transaction is dated after the statement period ends (March 31, 2024). Find it and flag it.
3. wire_confirmation_number should be null with a note that it isn't present in the source — the statement only says "see wire confirmation on file," it never states an actual number. Don't invent one.

Re-extract with these corrections.
```
This is the retry-with-error-feedback pattern: the errors are specific (the exact dollar amount, "after the statement period," "don't invent one") rather than a generic "try again." The corrected extraction should tag both `STARLIGHT CINEMA` lines with `detected_pattern: "possible_duplicate_charge"` (the statement's own footer explains duplicate lines can occur from separate authorization holds), set `conflict_detected: true` on the `04/02/2024` transaction, and set `wire_confirmation_number` to `null`.

### 3. Confirm which fix retrying could and couldn't produce
```
Which of the three corrections from my last message did you make by re-reading and re-reasoning about the statement, and which one was impossible to fix no matter how the request was worded — because the information simply isn't in the document? Explain why retrying doesn't help for that one.
```
Expect Claude to distinguish the duplicate-charge and out-of-period-date fixes (structural/semantic errors it could resolve by reconciling numbers and dates already present in the statement) from the wire confirmation number (retrying is ineffective here because no number exists anywhere in the source — the correct behavior is `null`, not a better guess).

### Checklist
- `calculated_total` (beginning balance + all in-period transactions, both duplicate lines counted): **$4,103.07**
- `stated_total` (printed ending balance): **$4,135.57**
- Discrepancy: **$32.50**, exactly one `STARLIGHT CINEMA` charge — the likely cause is a duplicate authorization hold, not a missing transaction
- Transaction outside the stated period: **04/02/2024 LAKEVIEW GAS STATION**, after the statement's own March 1-31 range
- `wire_confirmation_number`: **not present anywhere in the document** — correct output is `null`, not a fabricated value

---

# Implementation Info
> The sample file is a plain-text bank statement with a reconciliation gap, an out-of-period transaction, and a referenced-but-absent confirmation number. The README's three prompts extract, retry with specific validation errors, and then probe the retry/no-retry distinction.
## How each Task Info item is covered:
- Retry-with-error-feedback: appending specific validation errors on retry — `README.md`

  ```
  Your extraction has three problems:
  1. calculated_total and stated_total don't reconcile — they're off by exactly $32.50. ...
  2. One transaction is dated after the statement period ends (March 31, 2024). Find it and flag it.
  3. wire_confirmation_number should be null with a note that it isn't present in the source ...
  ```
  Prompt 2 names the exact dollar amount, the exact rule violated, and the exact field to null out, instead of a generic "this is wrong, try again."

- The limits of retry when information is absent from the source — `bank_statement_march_2024.txt`

  ```
  03/15/2024  Wire Transfer Out - INTL SUPPLIER PMT        -$450.00
              (ref: see wire confirmation on file)
  ```
  The statement references a confirmation number but never states it. Prompt 3 asks Claude to explain why no amount of re-reading fixes this, versus the duplicate-charge and date issues which are resolvable from data already in the document.

- detected_pattern field for systematic analysis of findings — `README.md`

  ```
  detected_pattern (null unless something about this line looks off, e.g. "possible_duplicate_charge", "date_outside_statement_period")
  ```
  Tagging each flagged line with a specific pattern name (rather than a bare boolean) lets a downstream reviewer see which pattern types keep getting dismissed as false positives, the same systematic-analysis motivation the task statement describes for code findings, applied here to transaction anomalies.

- Semantic validation errors vs schema syntax errors — `bank_statement_march_2024.txt`

  ```
  Ending Balance: $4,135.57
  ```
  Every field in prompt 1's schema is syntactically well-formed no matter what the model returns; the $32.50 gap between `calculated_total` and this printed `stated_total` is a semantic error — a value that doesn't reconcile — not a JSON-shape problem, and no schema constraint alone would have caught it.

- Follow-up requests including the original document, the failed extraction, and specific errors — `README.md`

  ```
  Read tasks/prompt-engineering/task-4-validation-retry-feedback-loops/bank_statement_march_2024.txt
  ...
  Your extraction has three problems: ...
  ```
  Because all three prompts run in one conversation, prompt 2's follow-up has the original statement (from prompt 1's read) and Claude's own failed extraction still in context, then adds the specific validation errors on top — the full self-correction shape, not just an error message in isolation.

- Identifying which retries succeed vs which are ineffective — `README.md`

  ```
  Which of the three corrections from my last message did you make by re-reading and re-reasoning about the statement, and which one was impossible to fix no matter how the request was worded ...
  ```
  Prompt 3 forces an explicit split between the two structural/semantic fixes (format and reconciliation errors, fixable) and the missing confirmation number (source data absent, not fixable by retrying).

- conflict_detected booleans for inconsistent source data, alongside calculated_total/stated_total discrepancy flagging — `README.md`

  ```
  calculated_total: the ending balance you get by adding every transaction in the statement period to the beginning balance
  stated_total: the ending balance printed on the statement
  ...
  conflict_detected (boolean, true if this line contradicts another part of the statement)
  ```
  The schema in prompt 1 asks for both totals side by side so the discrepancy is visible in the output itself, and a per-line `conflict_detected` flag for the out-of-period transaction, which contradicts the statement's own header period.
