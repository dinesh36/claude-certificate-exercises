"""
Exercise 1: Multi-Tool Agent with Escalation Logic
Domains: 1 (Agentic Architecture), 2 (Tool Design & MCP), 5 (Context Management & Reliability)

A customer-support agent with four tools (two of them deliberately similar —
get_order_details vs. search_orders — to test tool-selection accuracy),
structured tool error responses, a programmatic hook that blocks refunds
above a threshold and redirects to escalation, and a manual agentic loop
that terminates strictly on stop_reason.
"""

import os
import random
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

# Load the root-level .env (this exercise has no package/venv of its own —
# dependencies live in the repo-root uv project).
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

MODEL = "claude-opus-4-8"
REFUND_APPROVAL_THRESHOLD = 500.00

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# ---------------------------------------------------------------------------
# Mock data store
# ---------------------------------------------------------------------------

ORDERS = {
    "ORD-1001": {"customer_id": "CUST-1", "item": "Wireless Mouse", "amount": 29.99, "status": "delivered"},
    "ORD-1002": {"customer_id": "CUST-1", "item": "4K Monitor", "amount": 349.00, "status": "delivered"},
    "ORD-1003": {"customer_id": "CUST-2", "item": "Gaming Laptop", "amount": 1899.00, "status": "delivered"},
    "ORD-1004": {"customer_id": "CUST-2", "item": "USB Cable", "amount": 8.50, "status": "shipped"},
}

# Tracks which customer searches have already been retried, so search_orders
# can simulate one transient failure per customer and then succeed — this
# lets the agent's retry behavior on isRetryable errors be observed.
_search_attempts = {}


# ---------------------------------------------------------------------------
# Structured tool error helper (Domain 2)
# ---------------------------------------------------------------------------

def tool_error(error_category: str, is_retryable: bool, description: str) -> dict:
    """errorCategory is one of transient|validation|permission."""
    return {
        "errorCategory": error_category,
        "isRetryable": is_retryable,
        "description": description,
    }


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def get_order_details(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if order is None:
        return tool_error(
            "validation",
            False,
            f"No order found with ID '{order_id}'. Verify the order ID with the customer.",
        )
    return {"order_id": order_id, **order}


def search_orders(customer_id: str, query: str = "") -> dict:
    if customer_id not in {o["customer_id"] for o in ORDERS.values()}:
        return tool_error(
            "validation",
            False,
            f"No customer found with ID '{customer_id}'.",
        )

    # Simulate one transient failure per customer to exercise retry handling.
    attempts = _search_attempts.get(customer_id, 0)
    _search_attempts[customer_id] = attempts + 1
    if attempts == 0:
        return tool_error(
            "transient",
            True,
            "Order search service timed out. Retry the request.",
        )

    matches = [
        {"order_id": oid, **o}
        for oid, o in ORDERS.items()
        if o["customer_id"] == customer_id
        and (query.lower() in o["item"].lower() if query else True)
    ]
    return {"customer_id": customer_id, "matches": matches}


def process_refund(order_id: str, amount: float, reason: str) -> dict:
    order = ORDERS.get(order_id)
    if order is None:
        return tool_error(
            "validation",
            False,
            f"No order found with ID '{order_id}'. Cannot process refund.",
        )
    if amount > order["amount"]:
        return tool_error(
            "validation",
            False,
            f"Refund amount {amount} exceeds the order total {order['amount']}.",
        )
    return {
        "order_id": order_id,
        "refund_amount": amount,
        "status": "refund_processed",
        "reason": reason,
    }


def escalate_to_human(customer_id: str, issue_summary: str, root_cause: str, recommended_action: str, order_id: str = "") -> dict:
    ticket_id = f"ESC-{abs(hash((customer_id, issue_summary))) % 100000:05d}"
    return {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "order_id": order_id or None,
        "issue_summary": issue_summary,
        "root_cause": root_cause,
        "recommended_action": recommended_action,
        "status": "escalated_to_human_agent",
    }


TOOL_IMPLEMENTATIONS = {
    "get_order_details": get_order_details,
    "search_orders": search_orders,
    "process_refund": process_refund,
    "escalate_to_human": escalate_to_human,
}


# ---------------------------------------------------------------------------
# Tool schemas — get_order_details and search_orders are intentionally
# similar (both retrieve order info) and their descriptions carry the
# distinguishing boundary condition: exact ID in hand vs. not.
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_order_details",
        "description": (
            "Fetch full details for a SINGLE order when you already have its exact order ID "
            "(format 'ORD-XXXX'), e.g. because the customer provided it or a prior tool call "
            "returned it. Do NOT use this to browse or search — if you don't have an exact "
            "order ID yet, use search_orders instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Exact order ID, e.g. 'ORD-1003'."},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "search_orders",
        "description": (
            "Look up a customer's orders when you do NOT have an exact order ID — e.g. the "
            "customer describes an item or asks 'what did I order' without citing an order "
            "number. Requires the customer ID and returns all matching orders. Do NOT use this "
            "if an exact order ID is already known; call get_order_details instead. This tool "
            "can fail with a transient error — retry once if so."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Exact customer ID, e.g. 'CUST-2'."},
                "query": {"type": "string", "description": "Optional keyword to filter by item name."},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "process_refund",
        "description": (
            "Issue a refund for an order. Requires the order ID, the refund amount, and a reason. "
            "Refunds above a policy threshold are automatically blocked and redirected to human "
            "escalation — do not attempt to work around this by splitting a refund into smaller calls."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Exact order ID to refund."},
                "amount": {"type": "number", "description": "Refund amount in USD."},
                "reason": {"type": "string", "description": "Why the refund is being issued."},
            },
            "required": ["order_id", "amount", "reason"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Hand off the conversation to a human agent. Use this when a refund is blocked by "
            "policy, or when the issue cannot be resolved with the available tools. Produces a "
            "structured summary (root cause, recommended action) since the human agent has no "
            "access to this conversation transcript."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "order_id": {"type": "string", "description": "Related order ID, if any."},
                "issue_summary": {"type": "string", "description": "One-paragraph summary of the customer's issue."},
                "root_cause": {"type": "string", "description": "Diagnosed root cause of the issue."},
                "recommended_action": {"type": "string", "description": "What the human agent should do next."},
            },
            "required": ["customer_id", "issue_summary", "root_cause", "recommended_action"],
        },
    },
]

SYSTEM_PROMPT = (
    "You are a customer support agent for an online electronics retailer. "
    "Decompose multi-part requests into distinct concerns and address each one. "
    "Use get_order_details only when you have an exact order ID; use search_orders "
    "when you don't. If a refund is blocked by policy, escalate to a human agent "
    "with a structured handoff summary rather than retrying the refund. "
    "Retry tool calls that report a transient, retryable error; do not retry "
    "validation or permission errors — explain those to the customer instead."
)


# ---------------------------------------------------------------------------
# Programmatic hook (Domain 1.5): intercepts process_refund calls BEFORE
# execution and enforces the approval-threshold business rule deterministically,
# rather than relying on the model to remember and honor a prompt instruction.
# ---------------------------------------------------------------------------

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


def execute_tool(tool_name: str, tool_input: dict) -> tuple[dict, bool]:
    """Returns (result_payload, is_error)."""
    blocked = enforce_refund_policy(tool_name, tool_input)
    if blocked is not None:
        return blocked, True

    impl = TOOL_IMPLEMENTATIONS.get(tool_name)
    if impl is None:
        return tool_error("validation", False, f"Unknown tool '{tool_name}'."), True

    result = impl(**tool_input)
    is_error = isinstance(result, dict) and "errorCategory" in result
    return result, is_error


# ---------------------------------------------------------------------------
# Agentic loop (Domain 1.1): continues while stop_reason == "tool_use",
# terminates on "end_turn". No arbitrary iteration cap as the primary
# stopping mechanism, and no parsing of assistant text to detect completion.
# ---------------------------------------------------------------------------

def run_agent(user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result, is_error = execute_tool(block.name, block.input)
            print(f"  [tool] {block.name}({block.input}) -> {result}")
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                    "is_error": is_error,
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return "".join(block.text for block in response.content if block.type == "text")


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
    final_reply = run_agent(scenario)
    print(f"\nAgent: {final_reply}")
