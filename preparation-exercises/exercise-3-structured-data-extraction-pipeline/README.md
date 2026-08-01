# Preparation Exercise 3: Build a Structured Data Extraction Pipeline

**Objective:** Practice designing JSON schemas, using tool_use for structured output, implementing validation-retry loops, and designing batch processing strategies.

**Steps:**
1. Define an extraction tool with a JSON schema containing required and optional fields, an enum with an "other" + detail string pattern, and nullable fields for information that may not exist in source documents. Process documents where some fields are absent and verify the model returns null rather than fabricating values.
2. Implement a validation-retry loop: when Pydantic or JSON schema validation fails, send a follow-up request including the document, the failed extraction, and the specific validation error. Track which errors are resolvable via retry (format mismatches) versus which are not (information absent from source).
3. Add few-shot examples demonstrating extraction from documents with varied formats (e.g., inline citations vs bibliographies, narrative descriptions vs structured tables) and verify improved handling of structural variety.
4. Design a batch processing strategy: submit a batch of 100 documents using the Message Batches API, handle failures by custom_id, resubmit failed documents with modifications (e.g., chunking oversized documents), and calculate total processing time relative to SLA constraints.
5. Implement a human review routing strategy: have the model output field-level confidence scores, route low-confidence extractions to human review, and analyze accuracy by document type and field to verify consistent performance.

---

# Subject

NestList, an MLS aggregator, ingests real-estate listings in two source formats -- structured MLS feed sheets and narrative agent descriptions -- and normalizes both into one schema before next-day publishing.

- All 5 steps require the Prompt & Extraction Pipeline Tasks escape hatch (forced `tool_choice` and the Message Batches API have no chat-UI equivalent), so this is one coherent scripted pipeline, not manual prompts.

---

# How to run

See the repository root [README](../../README.md) for one-time setup (`uv` project, `ANTHROPIC_API_KEY`).

```bash
uv run preparation-exercises/exercise-3-structured-data-extraction-pipeline/main.py
```
Runs all three demos below in sequence. Each is also runnable on its own:
```bash
uv run preparation-exercises/exercise-3-structured-data-extraction-pipeline/main.py extract
uv run preparation-exercises/exercise-3-structured-data-extraction-pipeline/main.py batch
uv run preparation-exercises/exercise-3-structured-data-extraction-pipeline/main.py calibrate
```

**Verification status:** the Anthropic API key backing this environment (`client.messages.create`, used by `extract` and `batch`) is currently out of credit -- both modes fail with the same `BadRequestError: credit balance too low` seen elsewhere in this repo's recent history. The `calibrate` mode's one live call goes through the `claude` CLI instead (a separately authenticated session), and that call **did** succeed live -- its real output is below. For `extract`/`batch`, what's been verified directly instead: the Pydantic model rejects every case it should (missing `property_type_other_detail` when `other`, a non-numeric `price`) and accepts every case it should; a mocked-client run of the actual retry loop confirms it detects a validation failure, feeds the exact error + original document back with `is_error: true`, and succeeds on the second attempt; and `listing-40303`'s real per-document token-budget bug (see Step 4) deterministically computes `max_tokens=0`, confirmed by direct calculation. Re-run `extract`/`batch` once credits are available, rather than trusting the mocked-client check as a substitute for the real thing.

---

# Implementation Info

> `tools.py` holds the raw tool schema. `validation.py` is the Pydantic model plus retry-error classification. `batch.py` is the Batches API mechanics. `calibrate.py` is the confidence-routing analysis. `data.py` holds every sample document and the labeled validation set. `main.py` orchestrates all three demos.

## How each Step is covered:

- **Step 1 — Define an extraction tool with a JSON schema containing required and optional fields, an enum with an "other" + detail string pattern, and nullable fields; process documents where some fields are absent and verify the model returns null rather than fabricating values** — `tools.py`

  ```python
  "property_type": {
      "type": "string",
      "enum": ["single_family", "condo", "townhouse", "multi_family", "other"],
      "description": "Use 'other' for any property type that doesn't cleanly match one of these buckets.",
  },
  "property_type_other_detail": {
      "type": ["string", "null"],
      "description": (
          "Required (non-null) when property_type is 'other' -- quote or paraphrase the "
          "actual stated type. Null whenever property_type is not 'other'."
      ),
  },
  "square_footage": {
      "type": ["integer", "null"],
      "description": "Interior square footage, if stated. Null if the document doesn't mention it.",
  },
  ```

  `listing_id`/`address`/`price`/`property_type` are required; `square_footage`/`year_built`/`hoa_fee_monthly`/`bedrooms`/`bathrooms` are optional and nullable. `data.py`'s `TEST_NARRATIVE_UNSEEN` (a lighthouse-cottage listing with no stated square footage or year built) is the case that tests whether the model leaves those genuinely null instead of guessing.

- **Step 2 — Implement a validation-retry loop: when validation fails, send a follow-up including the document, the failed extraction, and the specific validation error; track resolvable (format) vs. unresolvable (information absent) errors** — `validation.py`, `main.py`

  ```python
  @model_validator(mode="after")
  def _other_requires_detail(self) -> "ListingExtraction":
      if self.property_type == "other" and not self.property_type_other_detail:
          raise ValueError(
              "property_type_other_detail is required (non-null) when property_type is 'other'."
          )
      ...
  ```
  ```python
  messages += [
      {"role": "assistant", "content": [{"type": "tool_use", "id": tool_use.id, ...}]},
      {"role": "user", "content": [{
          "type": "tool_result", "tool_use_id": tool_use.id,
          "content": f"That extraction failed validation: {last_error}\nOriginal document:\n{document_text}\n...",
          "is_error": True,
      }]},
  ]
  ```

  Verified with a mocked client (not shipped in the task folder): a first bad extraction (`property_type: "other"` with no detail) is fed back verbatim with `is_error: true`, and a corrected second attempt succeeds -- `attempts: 2` in the returned report. `classify_error` in `validation.py` labels a `property_type_other_detail`/enum/type failure `"resolvable"` (the model can fix the format on retry) versus everything else `"unresolvable"` (the source document genuinely doesn't state the value, so the fix is a null field, not a retry).

- **Step 3 — Add few-shot examples demonstrating extraction from documents with varied formats (inline citations vs. bibliographies, narrative vs. tables); verify improved handling of structural variety** — `main.py`, `data.py`

  ```python
  return [
      {"role": "user", "content": FEW_SHOT_MLS_SHEET},
      {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_fewshot_mls", "name": "extract_listing", "input": FEW_SHOT_MLS_EXTRACTION}]},
      {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_fewshot_mls", "content": "Recorded."}]},
      {"role": "user", "content": FEW_SHOT_NARRATIVE},
      ...
  ]
  ```

  Real conversation-turn few-shot (an actual `tool_use`/`tool_result` pair per example), not prose-described examples -- so the demonstration exercises `tool_use` the same way the real extraction call does. One example is a structured MLS sheet, the other a narrative description; `TEST_NARRATIVE_UNSEEN` is a third narrative listing with an "other" property type neither worked example shows, testing generalization rather than memorization of the two exact cases seen.

- **Step 4 — Design a batch processing strategy: submit 100 documents via the Message Batches API, handle failures by `custom_id`, resubmit failed documents with modifications, and calculate total processing time relative to SLA constraints** — `batch.py`, `main.py`, `data.py`

  ```python
  def _buggy_max_tokens_for(document_text: str) -> int:
      """Reserves 150 response tokens per numeric mention (price, sqft, year,
      etc.) in the document, assuming every listing states at least two such
      numbers. listing-40303 states only one ("$199,000") -- (1 - 1) * 150
      rounds the budget all the way to zero, an invalid max_tokens value the
      API genuinely rejects."""
      numeric_mentions = len(re.findall(r"\$?\d[\d,]*", document_text))
      return 150 * (numeric_mentions - 1)
  ```

  `listing-40303` ("Lighthouse Point Way. Listed at $199,000.") has exactly one numeric mention, confirmed by direct calculation to compute `max_tokens=0` -- a real per-document sizing bug, not a staged failure. The run detects it by `custom_id`, resubmits with `_fixed_max_tokens_for`'s sane floor, and reports total elapsed time against `BATCH_SUBMITTED_AT`/`BATCH_DEADLINE_AT` (a weekly data-quality review, Friday evening for a Monday deadline -- `meets_batch_sla` computes a +34h margin over the batch's up-to-24-hour window). The 6-listing batch's measured per-document time is then extrapolated to a full 100-listing batch as an explicit planning estimate, not a guarantee, since the Batch API has no per-document latency SLA of its own.

- **Step 5 — Implement a human review routing strategy: have the model output field-level confidence scores, route low-confidence extractions to human review, and analyze accuracy by document type and field to verify consistent performance** — `calibrate.py`, `data.py`

  ```python
  SEGMENT_ACCURACY = {
      ...
      ("narrative", "square_footage"): 0.52,
      ...
  }
  ```

  A real run's 93.6% aggregate accuracy across 280 labeled extractions hides a `narrative / square_footage` segment at only 50.0% -- narrative agent descriptions almost never state an exact interior square footage, but the model stays confident anyway. `calibrate_thresholds` correctly assigns that segment `"always_review"` (it can never reach 95% precision at any confidence cutoff), and `route_todays_queue` sends today's `narrative/square_footage` items to review even at 0.88-0.90 confidence, despite a healthy-looking number. The one live confidence check (`get_live_confidence_extraction`, via `claude -p`) actually ran: asked to extract `square_footage` from a real narrative listing that never states a number, it correctly reported `{"value": null, "confidence": 0.0}` rather than guessing.
