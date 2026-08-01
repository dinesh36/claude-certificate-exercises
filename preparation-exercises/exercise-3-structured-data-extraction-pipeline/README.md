# Preparation Exercise 3: Build a Structured Data Extraction Pipeline

> **Objective:** Practice designing JSON schemas, using tool_use for structured output, implementing validation-retry loops, and designing batch processing strategies.
> **Domains reinforced:** [Domain 4](../../wiki/tasks/4-prompt-engineering) (Prompt Engineering & Structured Output), [Domain 5](../../wiki/tasks/5-context-management) (Context Management & Reliability)

Source: [`wiki/tasks/6-preparation-exercises.md`](../../wiki/tasks/6-preparation-exercises.md), Exercise 3.

---

## Status: Fully covered

Every step below has a direct, near-1:1 implemented task — no new implementation needed.

## How each step is covered

- **Step 1 — Define an extraction tool with a JSON schema containing required and optional fields, an enum with an "other" + detail string pattern, and nullable fields; process documents where some fields are absent and verify the model returns null rather than fabricating values** — [`tasks/prompt-engineering/task-3-structured-output-tool-schemas`](../../tasks/prompt-engineering/task-3-structured-output-tool-schemas/README.md)

  An accounting firm's document intake receives invoices, purchase orders, and receipts of unknown type. `main.py` forces `extract_metadata` first, then sets `tool_choice: "any"` across three type-specific schemas so the model picks the right one without being told the document's type in advance — the exact required/optional/nullable-field shape this step asks for.

- **Step 2 — Implement a validation-retry loop: when validation fails, send a follow-up including the document, the failed extraction, and the specific validation error; track resolvable (format) vs. unresolvable (information absent) errors** — [`tasks/prompt-engineering/task-4-validation-retry-feedback-loops`](../../tasks/prompt-engineering/task-4-validation-retry-feedback-loops/README.md)

  A bank statement extraction pipeline built with three deliberate problems: a duplicated line item that breaks the reconciled total by a traceable amount, a transaction dated outside the statement's own period, and a referenced wire confirmation number that never actually appears in the document — a real retry-and-reconcile loop, not a staged validation failure.

- **Step 3 — Add few-shot examples demonstrating extraction from documents with varied formats (inline citations vs. bibliographies, narrative vs. tables); verify improved handling of structural variety** — [`tasks/prompt-engineering/task-2-few-shot-consistency`](../../tasks/prompt-engineering/task-2-few-shot-consistency/README.md)

  A recipe ingredient extractor pulls structured data from two source formats (a bulleted recipe card and a handwritten prose note), including informal measurements that should extract as `null`, a standardized casual unit that should NOT be nulled out ("a stick of butter" = 8 tbsp), and one casual unit never shown in any worked example — testing generalization, not memorization.

- **Step 4 — Design a batch processing strategy: submit 100 documents via the Message Batches API, handle failures by `custom_id`, resubmit failed documents with modifications, and calculate total processing time relative to SLA constraints** — [`tasks/prompt-engineering/task-5-batch-processing-strategies`](../../tasks/prompt-engineering/task-5-batch-processing-strategies/README.md)

  A legal team's weekly vendor-contract renewal-risk audit, submitted Friday for a Monday deadline. One contract's request is broken by a real per-paragraph sizing bug (not a staged failure) — the run detects it by `custom_id` and resubmits just that document with the bug fixed, then checks total turnaround against the SLA.

- **Step 5 — Implement a human review routing strategy: have the model output field-level confidence scores, route low-confidence extractions to human review, and analyze accuracy by document type and field to verify consistent performance** — [`tasks/context-management/task-5-stratified-confidence-calibration`](../../tasks/context-management/task-5-stratified-confidence-calibration/README.md)

  An HR platform's resume/video-interview screening pipeline. A real run's 93.3% aggregate accuracy across 210 labeled extractions hid a `video_transcript / years_experience` segment at only 60.0% — over 33 points below what the aggregate alone would show — and the pipeline routes today's queue into auto-approved, sent-to-review, and deferred buckets under a calibrated per-segment threshold and limited reviewer capacity.
