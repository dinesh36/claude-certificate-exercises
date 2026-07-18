"""Mock warehouse-fulfillment data for the structured-error MCP server (Domain 2.2).

INVENTORY backs search_inventory/reserve_stock. ORDERS backs ship_order/
check_carrier_status. AUTHORIZED_MANAGERS and APPROVAL_THRESHOLD_USD back
ship_order's permission check. FLAKY_REGIONS_FOR_ORDER deterministically
decides which carrier regions check_carrier_status simulates as unreachable
after local retries — ORDER-777 has one flaky region (partial-result path),
ORDER-999 has all regions flaky (all-unreachable / transient-error path),
every other order has none (fully healthy path).
"""

INVENTORY = {
    "SKU-1001": {"name": "Wireless Mouse", "stock": 42},
    "SKU-1042": {"name": "Mechanical Keyboard", "stock": 12},
    "SKU-2005": {"name": "USB-C Hub", "stock": 0},
}

APPROVAL_THRESHOLD_USD = 500.0
AUTHORIZED_MANAGERS = {"MGR-001", "MGR-002"}

ORDERS = {
    "ORDER-500": {"sku": "SKU-1001", "quantity": 2, "value_usd": 45.0},
    "ORDER-501": {"sku": "SKU-1042", "quantity": 3, "value_usd": 1250.0},
    "ORDER-777": {"sku": "SKU-2005", "quantity": 1, "value_usd": 30.0},
    "ORDER-999": {"sku": "SKU-1001", "quantity": 1, "value_usd": 20.0},
}

CARRIER_REGIONS = ["region-east", "region-west", "region-central"]

FLAKY_REGIONS_FOR_ORDER = {
    "ORDER-777": {"region-west"},
    "ORDER-999": {"region-east", "region-west", "region-central"},
}
