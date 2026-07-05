"""
Exercise 1: Multi-Tool Agent with Escalation Logic
Domains: 1 (Agentic Architecture), 2 (Tool Design & MCP), 5 (Context Management & Reliability)

A customer-support agent with four tools (two of them deliberately similar —
get_order_details vs. search_orders — to test tool-selection accuracy),
structured tool error responses, a programmatic hook that blocks refunds
above a threshold and redirects to escalation, and a manual agentic loop
that terminates strictly on stop_reason.

See tools.py for the tool schemas/implementations, policy.py for the
refund-threshold hook, and data.py for the mock order store.
"""

import sys

from common.agent_loop import run_tool_loop
from common.client import DEFAULT_MODEL, get_client

from policy import enforce_refund_policy
from tools import TOOLS, dispatch_tool

client = get_client()

SYSTEM_PROMPT = (
    "You are a customer support agent for an online electronics retailer. "
    "Decompose multi-part requests into distinct concerns and address each one. "
    "Use get_order_details only when you have an exact order ID; use search_orders "
    "when you don't. If a refund is blocked by policy, escalate to a human agent "
    "with a structured handoff summary rather than retrying the refund. "
    "Retry tool calls that report a transient, retryable error; do not retry "
    "validation or permission errors — explain those to the customer instead."
)


if __name__ == "__main__":
    scenario = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "Hi, I have two things. First, order ORD-1003 arrived defective and I want a full "
            "refund. Second, can you check what else customer CUST-2 has ordered recently?"
        )
    )
    print(f"User: {scenario}\n")
    result = run_tool_loop(
        client=client,
        model=DEFAULT_MODEL,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        dispatcher=dispatch_tool,
        user_message=scenario,
        hook=enforce_refund_policy
    )
    print(f"\nAgent: {result.final_text}")
