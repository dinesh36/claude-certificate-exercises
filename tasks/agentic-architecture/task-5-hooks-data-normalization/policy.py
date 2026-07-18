"""Programmatic policy hook (Domain 1.5).

Intercepts issue_shipping_credit calls BEFORE execution and enforces the
credit-threshold business rule deterministically — a PreToolUse-style gate
— rather than relying on the model to remember and honor a prompt instruction.
"""

from common.errors import tool_error

CREDIT_APPROVAL_THRESHOLD = 75.00


def enforce_credit_threshold(tool_name: str, tool_input: dict) -> dict | None:
    if tool_name != "issue_shipping_credit":
        return None
    amount = tool_input.get("amount")
    if isinstance(amount, (int, float)) and amount > CREDIT_APPROVAL_THRESHOLD:
        return tool_error(
            "permission",
            False,
            (
                f"Credit amount {amount} exceeds the ${CREDIT_APPROVAL_THRESHOLD:.2f} threshold "
                "a human claims-desk agent must approve. Blocked by policy hook — escalate to "
                "escalate_to_claims_desk instead of retrying issue_shipping_credit."
            ),
        )
    return None
