# Task Statement 4.3: Enforce structured output using tool use and JSON schemas

## Knowledge of
- Tool use (tool_use) with JSON schemas as the most reliable approach for guaranteed schema-compliant structured output, eliminating JSON syntax errors
- The distinction between tool_choice: "auto" (model may return text instead of calling a tool), "any" (model must call a tool but can choose which), and forced tool selection (model must call a specific named tool)
- That strict JSON schemas via tool use eliminate syntax errors but do not prevent semantic errors (e.g., line items that don't sum to total, values in wrong fields)
- Schema design considerations: required vs optional fields, enum fields with "other" + detail string patterns for extensible categories

## Skills in
- Defining extraction tools with JSON schemas as input parameters and extracting structured data from the tool_use response
- Setting tool_choice: "any" to guarantee structured output when multiple extraction schemas exist and the document type is unknown
- Forcing a specific tool with tool_choice: {"type": "tool", "name": "extract_metadata"} to ensure a particular extraction runs before enrichment steps
- Designing schema fields as optional (nullable) when source documents may not contain the information, preventing the model from fabricating values to satisfy required fields
- Adding enum values like "unclear" for ambiguous cases and "other" + detail fields for extensible categorization
- Including format normalization rules in prompts alongside strict output schemas to handle inconsistent source formatting

---

# Subject

An accounting firm's document intake receives invoices, purchase orders, and receipts of unknown type, in inconsistent formats. This task is scripted (the escape-hatch shape for this domain), because `tool_choice` is a Messages API request parameter with no chat-UI equivalent a person could exercise by typing a prompt.

- `main.py` always forces `extract_metadata` first (sender, date, document ID), then sets `tool_choice: "any"` across three type-specific schemas so the model picks the right one without being told the document's type in advance.
- One sample invoice's line items don't sum to its stated total — a real semantic error a schema-valid extraction can't catch on its own.

---

# How to run

See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run tasks/prompt-engineering/task-3-structured-output-tool-schemas/main.py
```
```bash
uv run tasks/prompt-engineering/task-3-structured-output-tool-schemas/main.py purchase_order_missing_date
```
```bash
uv run tasks/prompt-engineering/task-3-structured-output-tool-schemas/main.py receipt_clean
```
The first (default) run exercises the invoice with the semantic mismatch. The second exercises a document missing an optional field (`requested_delivery_date`) and a non-enum approval status. The third exercises a document where the line items *do* sum correctly, and a non-enum payment method — a contrast case showing the semantic check only fires when there's an actual discrepancy.

---

# Implementation Info

> `tools.py` holds the raw tool schemas (`METADATA_TOOL`, `EXTRACTION_TOOLS`) — no implementation callables, since `main.py` reads `tool_use.input` directly via `common/tool_use.py`'s shared reader. `data.py` holds three sample documents. `main.py` runs the two-stage pipeline and the semantic-consistency check.

## How each Task Info item is covered:

- **Tool use + JSON schemas guarantee schema-compliant output** — `tools.py`

  ```python
  METADATA_TOOL = {
      "name": "extract_metadata",
      "description": (
          "Extract identifying metadata from an incoming accounting document. "
          "Always run this before any type-specific extraction."
      ),
      "input_schema": {
  ```
  Every extraction happens through a `tool_use` call against one of these schemas — `main.py` never asks the model to emit JSON as free text, so there's no `JSON.parse`/`json.loads` risk on the shape itself. A real run's `extraction_fields` always validates against its tool's schema (see `run_pipeline`'s output above).

- **tool_choice: auto vs any vs forced-named** — `main.py`

  ```python
  tool_choice={"type": "tool", "name": "extract_metadata"},
  ...
  tool_choice={"type": "any"},
  ```
  The two calls in `run_pipeline` contrast the two `tool_choice` modes this pipeline actually needs: forced-named for the metadata stage (must always be this exact tool), and `"any"` for the type-specific stage (must call some tool, but which one depends on the document). `"auto"` is deliberately never used here — this pipeline always needs a guaranteed tool call, not an optional one.

- **Strict schemas eliminate syntax errors, not semantic errors** — `main.py`

  ```python
  def check_semantic_consistency(extraction_fields: dict) -> str | None:
      """A strict schema guarantees valid JSON, not correct arithmetic — check separately."""
      line_items = extraction_fields.get("line_items")
      stated_total = extraction_fields.get("stated_total")
  ```
  A real run against `invoice_mismatch` returned a perfectly schema-valid `extraction_fields` — `stated_total: 1300.0` — even though the line items actually sum to `1240.0`. The schema alone never catches this; `check_semantic_consistency` is a separate, explicit check.

- **Schema design: required vs optional fields, enum + "other"/detail pattern** — `tools.py`

  ```python
  "payment_terms": {
      "type": "string",
      "enum": ["net_15", "net_30", "net_60", "other"],
      "description": "Use 'other' for any terms that don't cleanly match one of these buckets.",
  },
  "payment_terms_detail": {
      "type": ["string", "null"],
      "description": "Required (non-null) when payment_terms is 'other' — quote or paraphrase the actual stated terms.",
  },
  ```
  `payment_terms` (invoice), `approval_status` (purchase order), and `payment_method` (receipt) each follow the same enum + `other`/`_detail` pattern. A real run against `invoice_mismatch` — whose actual terms are "Net 30, plus a 2% early-payment discount" — correctly returned `payment_terms: "other"` with the real terms quoted in `payment_terms_detail`, rather than being forced into `net_30`.

- **Defining extraction tools and reading the tool_use response** — `../../../common/tool_use.py`

  ```python
  def first_tool_use_block(response: Any) -> Any:
      """Return the first tool_use content block in a response.

      Raises ValueError (naming the actual stop_reason) if the model replied
      with text instead of calling a tool — e.g. a forced or "any" tool_choice
      the model still didn't satisfy.
      """
      for block in response.content:
          if block.type == "tool_use":
              return block
      raise ValueError(f"model did not call a tool (stop_reason={response.stop_reason})")
  ```
  Both pipeline stages in `main.py` call this shared helper to pull the structured `input` off the response's `tool_use` content block — never off parsed free text. It lives in `common/` rather than this task folder since any future script that calls `tools=`/`tool_choice=` directly (bypassing `common/agent_loop.py`'s loop) needs the exact same read.

- **tool_choice: "any" for an unknown document type** — `main.py`

  ```python
  extraction_response = client.messages.create(
      model=DEFAULT_MODEL,
      max_tokens=1024,
      system=SYSTEM_PROMPT,
      tools=EXTRACTION_TOOLS,
      tool_choice={"type": "any"},
  ```
  `EXTRACTION_TOOLS` holds all three type-specific schemas at once. A real run correctly picked `extract_invoice` for the invoice, `extract_purchase_order` for the purchase order, and `extract_receipt` for the receipt — the model chose, nothing in the code named the type in advance.

- **Forcing extract_metadata before type-specific extraction** — `main.py`

  ```python
  metadata_response = client.messages.create(
      model=DEFAULT_MODEL,
      max_tokens=1024,
      system=SYSTEM_PROMPT,
      tools=[METADATA_TOOL],
      tool_choice={"type": "tool", "name": "extract_metadata"},
  ```
  This call always runs first in `run_pipeline`, regardless of document type — the coordinator-side enrichment step (metadata) is guaranteed before the type-specific extraction runs.

- **Optional (nullable) fields prevent fabrication** — `tools.py`

  ```python
  "document_id": {
      "type": ["string", "null"],
      "description": (
          "An invoice/PO/receipt number, only if the document actually "
          "states one. Null if none is stated — never invent one."
      ),
  },
  ```
  Neither `document_id` nor `requested_delivery_date` is in its tool's `required` list, and both allow `null`. A real run against `invoice_mismatch` (which never states an invoice number) returned `document_id: null` instead of a fabricated one; a real run against `purchase_order_missing_date` omitted `requested_delivery_date` entirely rather than inventing a date.

- **Enum "unclear"/"other" for ambiguous and extensible categories** — `tools.py`

  ```python
  "currency": {
      "type": "string",
      "enum": ["usd", "eur", "gbp", "unclear"],
      "description": "Use 'unclear' if the currency isn't stated unambiguously (e.g. only a bare '$' symbol).",
  },
  ```
  `invoice_mismatch` only ever uses a bare `$` symbol, never naming a currency — a real run correctly returned `currency: "unclear"` rather than guessing `"usd"`.

- **Format normalization rules alongside a strict schema** — `main.py`

  ```python
  SYSTEM_PROMPT = (
      "You are a document-intake assistant for an accounting firm. Always normalize "
      "any date you extract to YYYY-MM-DD, regardless of the source document's format. "
  ```
  The three sample documents state their dates as `"March 14, 2024"`, `"2024-03-20"`, and `"14 Mar 2024"` — three different formats. Real runs against all three returned `document_date: "2024-03-14"` / `"2024-03-20"` / `"2024-03-14"` respectively — every one normalized to the same `YYYY-MM-DD` shape the schema expects.
