"""Tool schemas and implementations (Domain 2).

get_order_details and search_orders are deliberately similar — both
retrieve order info — so their descriptions carry the distinguishing
boundary condition (exact ID in hand vs. not) to test tool-selection
accuracy rather than relying on the model to guess.
"""

from common.errors import tool_error

from data import ORDERS, _search_attempts

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
# Tool schemas
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


def dispatch_tool(tool_name: str, tool_input: dict) -> dict:
    impl = TOOL_IMPLEMENTATIONS.get(tool_name)
    if impl is None:
        return tool_error("validation", False, f"Unknown tool '{tool_name}'.")
    return impl(**tool_input)
