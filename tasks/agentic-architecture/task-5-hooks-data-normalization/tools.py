"""Tool schemas and implementations for the shipment-tracking desk (Domain 1.5).

Each _check_*_status implementation returns whatever raw shape that
carrier's own system would actually return — a different one per carrier.
Nothing in here normalizes them; that's normalize.py's PostToolUse hook's
job, applied by common/agent_loop.py after the implementation returns and
before the model ever sees the result.

The only export is TOOLS: a list of {"schema": ..., "implementation": ...}
entries. common/agent_loop.py extracts the schemas for the Anthropic API call
and builds its own name -> implementation map to dispatch tool_use blocks
directly — nothing else in this module needs to be imported elsewhere.
"""

from common.errors import tool_error

from data import (
    CREDITS_ISSUED,
    FEDEX_TRACKING,
    LEGACY_TRACKING,
    REGIONAL_TRACKING,
)

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _check_fedex_status(tracking_id: str) -> dict:
    record = FEDEX_TRACKING.get(tracking_id)
    if record is None:
        return tool_error("validation", False, f"No FedEx-style tracking record found for '{tracking_id}'.")
    return {"tracking_id": tracking_id, "epoch_ts": record["epoch_ts"], "code": record["code"]}


def _check_regional_courier_status(tracking_id: str) -> dict:
    record = REGIONAL_TRACKING.get(tracking_id)
    if record is None:
        return tool_error("validation", False, f"No regional-courier tracking record found for '{tracking_id}'.")
    return {"tracking_id": tracking_id, "timestamp": record["timestamp"], "status": record["status"]}


def _check_legacy_carrier_status(tracking_id: str) -> dict:
    record = LEGACY_TRACKING.get(tracking_id)
    if record is None:
        return tool_error("validation", False, f"No legacy-carrier tracking record found for '{tracking_id}'.")
    return {"tracking_id": tracking_id, "date_str": record["date_str"], "status_flag": record["status_flag"]}


def _issue_shipping_credit(tracking_id: str, amount: float, reason: str) -> dict:
    # Only reachable if policy.py's hook let it through — see enforce_credit_threshold.
    if tracking_id not in {**FEDEX_TRACKING, **REGIONAL_TRACKING, **LEGACY_TRACKING}:
        return tool_error("validation", False, f"No tracking record found for '{tracking_id}'.")
    CREDITS_ISSUED[tracking_id] = CREDITS_ISSUED.get(tracking_id, 0.0) + amount
    return {"tracking_id": tracking_id, "credited_amount": amount, "reason": reason, "status": "credit_issued"}


def _escalate_to_claims_desk(
    tracking_id: str, issue_summary: str, root_cause: str, recommended_action: str
) -> dict:
    ticket_id = f"CLM-{abs(hash((tracking_id, issue_summary))) % 100000:05d}"
    return {
        "ticket_id": ticket_id,
        "tracking_id": tracking_id,
        "issue_summary": issue_summary,
        "root_cause": root_cause,
        "recommended_action": recommended_action,
        "status": "escalated_to_claims_desk",
    }


# ---------------------------------------------------------------------------
# TOOLS — the only export: one {schema, implementation} entry per tool
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "schema": {
            "name": "check_fedex_status",
            "description": (
                "Check delivery status for a tracking ID from the FedEx-style carrier system "
                "(tracking IDs starting with 'FDX-'). Returns a raw Unix epoch timestamp and a "
                "numeric status code in this carrier's own format — do not interpret these "
                "yourself, they arrive already normalized into 'last_update'/'status'."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"tracking_id": {"type": "string", "description": "Tracking ID, e.g. 'FDX-1001'."}},
                "required": ["tracking_id"],
            },
        },
        "implementation": _check_fedex_status,
    },
    {
        "schema": {
            "name": "check_regional_courier_status",
            "description": (
                "Check delivery status for a tracking ID from the regional courier system "
                "(tracking IDs starting with 'RC-'). Returns an ISO 8601 timestamp and a "
                "free-text status string in this carrier's own wording — arrives already "
                "normalized into 'last_update'/'status'."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"tracking_id": {"type": "string", "description": "Tracking ID, e.g. 'RC-2002'."}},
                "required": ["tracking_id"],
            },
        },
        "implementation": _check_regional_courier_status,
    },
    {
        "schema": {
            "name": "check_legacy_carrier_status",
            "description": (
                "Check delivery status for a tracking ID from the legacy carrier system "
                "(tracking IDs starting with 'LG-'). Returns a custom date string and a "
                "single-letter status flag in this carrier's own format — arrives already "
                "normalized into 'last_update'/'status'."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"tracking_id": {"type": "string", "description": "Tracking ID, e.g. 'LG-3003'."}},
                "required": ["tracking_id"],
            },
        },
        "implementation": _check_legacy_carrier_status,
    },
    {
        "schema": {
            "name": "issue_shipping_credit",
            "description": (
                "Issue a shipping credit for a delayed or lost package. Credits above a policy "
                "threshold are automatically blocked and redirected to human claims-desk "
                "escalation — do not attempt to work around this by splitting a credit into "
                "smaller calls."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "tracking_id": {"type": "string", "description": "Tracking ID the credit is for."},
                    "amount": {"type": "number", "description": "Credit amount in USD."},
                    "reason": {"type": "string", "description": "Why the credit is being issued."},
                },
                "required": ["tracking_id", "amount", "reason"],
            },
        },
        "implementation": _issue_shipping_credit,
    },
    {
        "schema": {
            "name": "escalate_to_claims_desk",
            "description": (
                "Hand off the request to a human claims-desk agent. Use this when a credit is "
                "blocked by policy, or when the issue can't be resolved with the available "
                "tools. Produces a structured summary (root cause, recommended action) since "
                "the human has no access to this conversation transcript."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "tracking_id": {"type": "string"},
                    "issue_summary": {"type": "string", "description": "One-paragraph summary of the customer's issue."},
                    "root_cause": {"type": "string", "description": "Diagnosed root cause of the issue."},
                    "recommended_action": {"type": "string", "description": "What the claims-desk agent should do next."},
                },
                "required": ["tracking_id", "issue_summary", "root_cause", "recommended_action"],
            },
        },
        "implementation": _escalate_to_claims_desk,
    },
]
