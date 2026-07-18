"""Mock order data store for the task."""

ORDERS = {
    "ORD-1001": {"customer_id": "CUST-1", "item": "Wireless Mouse", "amount": 29.99, "status": "delivered"},
    "ORD-1002": {"customer_id": "CUST-1", "item": "4K Monitor", "amount": 349.00, "status": "delivered"},
    "ORD-1003": {"customer_id": "CUST-2", "item": "Gaming Laptop", "amount": 1899.00, "status": "delivered"},
    "ORD-1004": {"customer_id": "CUST-2", "item": "USB Cable", "amount": 8.50, "status": "shipped"},
}

# Tracks which customer searches have already been retried, so search_orders
# can simulate one transient failure per customer and then succeed — this
# lets the agent's retry behavior on isRetryable errors be observed.
_search_attempts: dict[str, int] = {}
