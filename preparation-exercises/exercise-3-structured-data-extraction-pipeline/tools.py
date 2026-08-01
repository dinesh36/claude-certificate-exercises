"""Preparation Exercise 3: Build a Structured Data Extraction Pipeline
Domains reinforced: 4 (Prompt Engineering & Structured Output), 5 (Context Management & Reliability)

Raw Anthropic tool schema for the real-estate listing-intake pipeline. No
implementation callable here -- main.py reads tool_use.input directly, the
same escape-hatch convention as tasks/prompt-engineering/task-3.
"""

EXTRACT_LISTING_TOOL = {
    "name": "extract_listing",
    "description": (
        "Extract structured data from a real-estate listing submission. Every field must be "
        "null (not fabricated) when the source document doesn't state it -- do not infer or "
        "estimate a value that isn't actually present."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "listing_id": {"type": "string", "description": "The listing's ID as stated, e.g. 'MLS-10234'."},
            "address": {"type": "string", "description": "Full street address as stated."},
            "price": {"type": "number", "description": "Asking price in USD, as a plain number (no '$' or commas)."},
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
            "year_built": {
                "type": ["integer", "null"],
                "description": "Year built, if stated. Null if not mentioned.",
            },
            "hoa_fee_monthly": {
                "type": ["number", "null"],
                "description": (
                    "Monthly HOA fee in USD, if stated. Null if the document doesn't mention an "
                    "HOA at all -- do not assume zero."
                ),
            },
            "bedrooms": {"type": ["integer", "null"], "description": "Number of bedrooms, if stated. Null if not mentioned."},
            "bathrooms": {
                "type": ["number", "null"],
                "description": "Number of bathrooms (e.g. 2.5 for two full + one half bath), if stated. Null if not mentioned.",
            },
            "field_confidence": {
                "type": "object",
                "description": (
                    "Your confidence (0.0-1.0) that each extracted field above is correct, keyed by "
                    "field name. Include an entry for every field above except field_confidence itself."
                ),
                "additionalProperties": {"type": "number"},
            },
        },
        "required": ["listing_id", "address", "price", "property_type", "field_confidence"],
    },
}
