"""Programmatic policy hook (Domain 1.5).

Intercepts process_refund calls BEFORE execution and enforces the
approval-threshold business rule deterministically, rather than relying
on the model to remember and honor a prompt instruction.
"""

from common.errors import tool_error

REFUND_APPROVAL_THRESHOLD = 500.00


def enforce_refund_policy(tool_name: str, tool_input: dict) -> dict | None:
    if tool_name != "process_refund":
        return None
    amount = tool_input.get("amount")
    if isinstance(amount, (int, float)) and amount > REFUND_APPROVAL_THRESHOLD:
        return tool_error(
            "permission",
            False,
            (
                f"Refund amount {amount} exceeds the ${REFUND_APPROVAL_THRESHOLD:.2f} threshold "
                "a human agent must approve. Blocked by policy hook — escalate to a human agent "
                "instead of retrying process_refund."
            ),
        )
    return None
