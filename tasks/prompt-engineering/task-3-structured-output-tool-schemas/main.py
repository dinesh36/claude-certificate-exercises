"""
Task 3: Structured Output Tool Schemas
Domain: Prompt Engineering & Structured Output

An accounting document-intake pipeline that enforces structured output via
tool_use and JSON schemas. Stage 1 forces the extract_metadata tool so
identifying fields always come back the same shape. Stage 2 sets
tool_choice: "any" across three type-specific extraction schemas, since the
document's type isn't known ahead of time. A final check demonstrates that a
strict schema guarantees valid JSON, not correct arithmetic.

See tools.py for the raw tool schemas and data.py for the sample documents.
"""

import json
import sys

from common.client import DEFAULT_MODEL, get_client
from common.tool_use import first_tool_use_block

from data import SAMPLE_DOCUMENTS
from tools import EXTRACTION_TOOLS, METADATA_TOOL

client = get_client()

SYSTEM_PROMPT = (
    "You are a document-intake assistant for an accounting firm. Always normalize "
    "any date you extract to YYYY-MM-DD, regardless of the source document's format. "
    "Never invent a value for a field the source document doesn't state — leave it "
    "null instead."
)


def run_pipeline(document_text: str) -> dict:
    """Runs the two-stage extraction and returns both tool_use results."""
    metadata_response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[METADATA_TOOL],
        tool_choice={"type": "tool", "name": "extract_metadata"},
        messages=[{"role": "user", "content": document_text}],
    )
    metadata = first_tool_use_block(metadata_response).input

    extraction_response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=EXTRACTION_TOOLS,
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": document_text}],
    )
    extraction_block = first_tool_use_block(extraction_response)

    return {
        "metadata": metadata,
        "extraction_tool": extraction_block.name,
        "extraction_fields": extraction_block.input,
    }


def check_semantic_consistency(extraction_fields: dict) -> str | None:
    """A strict schema guarantees valid JSON, not correct arithmetic — check separately."""
    line_items = extraction_fields.get("line_items")
    stated_total = extraction_fields.get("stated_total")
    if not line_items or stated_total is None:
        return None

    calculated_total = round(sum(item["amount"] for item in line_items), 2)
    if calculated_total != stated_total:
        return (
            f"schema-valid but semantically wrong: line items sum to "
            f"{calculated_total}, but stated_total is {stated_total}"
        )
    return None


def main(doc_name: str = "invoice_mismatch") -> None:
    document_text = SAMPLE_DOCUMENTS[doc_name]

    result = run_pipeline(document_text)
    print(json.dumps(result, indent=2))

    warning = check_semantic_consistency(result["extraction_fields"])
    if warning:
        print(f"\nWARNING: {warning}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "invoice_mismatch")
