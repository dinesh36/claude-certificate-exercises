"""Task 3: Structured Output Tool Schemas
Prompt Engineering & Structured Output
Raw Anthropic tool schemas for the accounting document-intake pipeline. No
implementation callables here — main.py reads tool_use.input directly.
"""

METADATA_TOOL = {
    "name": "extract_metadata",
    "description": (
        "Extract identifying metadata from an incoming accounting document. "
        "Always run this before any type-specific extraction."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sender": {
                "type": "string",
                "description": "The company or person that issued the document.",
            },
            "document_date": {
                "type": ["string", "null"],
                "description": (
                    "The document's date, normalized to YYYY-MM-DD regardless of "
                    "the source format (e.g. 'March 14, 2024' -> '2024-03-14')."
                ),
            },
            "document_id": {
                "type": ["string", "null"],
                "description": (
                    "An invoice/PO/receipt number, only if the document actually "
                    "states one. Null if none is stated — never invent one."
                ),
            },
            "document_type_guess": {
                "type": "string",
                "enum": ["invoice", "purchase_order", "receipt", "unclear"],
                "description": (
                    "Best guess at the document type. Use 'unclear' if the "
                    "document genuinely could be more than one type."
                ),
            },
        },
        "required": ["sender", "document_type_guess"],
    },
}

_LINE_ITEMS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "description": {"type": "string"},
            "amount": {"type": "number", "description": "Line amount in dollars."},
        },
        "required": ["description", "amount"],
    },
}

_EXTRACT_INVOICE_TOOL = {
    "name": "extract_invoice",
    "description": "Extract structured data from an invoice.",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {
                "type": ["string", "null"],
                "description": "Null if the invoice doesn't clearly state one.",
            },
            "line_items": _LINE_ITEMS_SCHEMA,
            "stated_total": {
                "type": "number",
                "description": "The total amount the invoice states is owed, in dollars.",
            },
            "currency": {
                "type": "string",
                "enum": ["usd", "eur", "gbp", "unclear"],
                "description": "Use 'unclear' if the currency isn't stated unambiguously (e.g. only a bare '$' symbol).",
            },
            "payment_terms": {
                "type": "string",
                "enum": ["net_15", "net_30", "net_60", "other"],
                "description": "Use 'other' for any terms that don't cleanly match one of these buckets.",
            },
            "payment_terms_detail": {
                "type": ["string", "null"],
                "description": "Required (non-null) when payment_terms is 'other' — quote or paraphrase the actual stated terms.",
            },
        },
        "required": [
            "line_items",
            "stated_total",
            "currency",
            "payment_terms",
        ],
    },
}

_EXTRACT_PURCHASE_ORDER_TOOL = {
    "name": "extract_purchase_order",
    "description": "Extract structured data from a purchase order.",
    "input_schema": {
        "type": "object",
        "properties": {
            "po_number": {"type": "string"},
            "line_items": _LINE_ITEMS_SCHEMA,
            "requested_delivery_date": {
                "type": ["string", "null"],
                "description": "Normalized to YYYY-MM-DD. Null if the PO doesn't state one.",
            },
            "approval_status": {
                "type": "string",
                "enum": ["approved", "pending", "rejected", "other"],
                "description": "Use 'other' for any status that doesn't cleanly match one of these buckets.",
            },
            "approval_status_detail": {
                "type": ["string", "null"],
                "description": "Required (non-null) when approval_status is 'other' — quote or paraphrase what the document actually says.",
            },
        },
        "required": ["po_number", "line_items", "approval_status"],
    },
}

_EXTRACT_RECEIPT_TOOL = {
    "name": "extract_receipt",
    "description": "Extract structured data from a receipt.",
    "input_schema": {
        "type": "object",
        "properties": {
            "merchant": {"type": "string"},
            "line_items": _LINE_ITEMS_SCHEMA,
            "stated_total": {"type": "number"},
            "payment_method": {
                "type": "string",
                "enum": ["cash", "credit_card", "debit_card", "other"],
                "description": "Use 'other' for any payment method that doesn't cleanly match one of these buckets.",
            },
            "payment_method_detail": {
                "type": ["string", "null"],
                "description": "Required (non-null) when payment_method is 'other' — quote or paraphrase what the receipt actually says.",
            },
        },
        "required": ["merchant", "line_items", "stated_total", "payment_method"],
    },
}

EXTRACTION_TOOLS = [
    _EXTRACT_INVOICE_TOOL,
    _EXTRACT_PURCHASE_ORDER_TOOL,
    _EXTRACT_RECEIPT_TOOL,
]
