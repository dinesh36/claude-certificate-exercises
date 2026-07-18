"""
Exercise 5: Multi-Carrier Shipment Tracking
Domain: 1 (Agentic Architecture & Orchestration) — Task Statement 1.5

A shipment-tracking desk that checks delivery status across three mock
carrier systems, each returning a different raw timestamp/status format.
A PostToolUse hook (normalize.py) rewrites every result into one consistent
shape before the model ever sees it, and a PreToolUse hook (policy.py)
deterministically blocks issue_shipping_credit above a threshold, redirecting
to human claims-desk escalation rather than leaving either rule to the prompt.

See data.py for the mock per-carrier records, tools.py for the tool
schemas/implementations, normalize.py for the result-normalization hook,
and policy.py for the credit-threshold hook.
"""

import sys

from common.agent_loop import run_tool_loop
from common.client import DEFAULT_MODEL, get_client

from normalize import normalize_carrier_result
from policy import enforce_credit_threshold
from tools import TOOLS, dispatch_tool

client = get_client()

SYSTEM_PROMPT = (
    "You are a shipment-tracking desk agent. Tracking IDs starting with "
    "'FDX-' use check_fedex_status, 'RC-' use check_regional_courier_status, "
    "and 'LG-' use check_legacy_carrier_status — every one of them returns "
    "results already normalized to the same status vocabulary (label_created, "
    "in_transit, out_for_delivery, delivered, exception) and an ISO 8601 "
    "last_update, so reason about them the same way regardless of carrier. "
    "Decompose requests about multiple packages into distinct checks. "
    "If a package's status is 'exception' and the customer wants "
    "compensation, you may issue_shipping_credit — credits above the policy "
    "threshold are automatically blocked and redirected to escalation; if "
    "that happens, do not retry issue_shipping_credit, escalate to "
    "escalate_to_claims_desk with a structured handoff instead."
)


if __name__ == "__main__":
    scenario = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Can you check on my two packages, FDX-1001 and RC-2002?"
    )
    print(f"User: {scenario}\n")
    result = run_tool_loop(
        client=client,
        model=DEFAULT_MODEL,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        dispatcher=dispatch_tool,
        user_message=scenario,
        hook=enforce_credit_threshold,
        post_hook=normalize_carrier_result,
    )
    print(f"\nAgent: {result.final_text}")
