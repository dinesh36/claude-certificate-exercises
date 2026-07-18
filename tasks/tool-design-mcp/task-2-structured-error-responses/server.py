"""
Task 2: Structured Error Responses
Domain: Tool Design & MCP Integration — Task Statement 2.2

A warehouse-fulfillment MCP server whose four tools deliberately exercise
every error category the task statement covers: reserve_stock and
search_inventory return validation errors (bad input, and a business-rule
violation — requesting more stock than is available — mapped to the same
"validation" category with a customer-friendly description), ship_order
returns a permission error (an order above the approval threshold without
an authorized manager ID), and check_carrier_status distinguishes local,
recoverable transient failures (retried internally, folded into a partial
result) from a genuinely unrecoverable one (every region down, raised as a
retryable transient error) — never a generic "Operation failed" string.

search_inventory also demonstrates the companion distinction the task
statement calls out: a query that matches nothing is a normal, successful
empty result, not an error — only an actually invalid query (e.g. blank)
raises.

See data.py for the mock inventory/order/carrier data this server reads
from, and common/errors.py's StructuredToolError for how a raised exception
carries errorCategory/isRetryable/description through FastMCP's isError flag
instead of a bare failure string.
"""

from mcp.server.fastmcp import FastMCP

from common.errors import StructuredToolError
from common.mcp_logging import logged_tool
from data import (
    APPROVAL_THRESHOLD_USD,
    AUTHORIZED_MANAGERS,
    CARRIER_REGIONS,
    FLAKY_REGIONS_FOR_ORDER,
    INVENTORY,
    ORDERS,
)

SERVER_NAME = "warehouse-fulfillment"

mcp = FastMCP(SERVER_NAME)


@mcp.tool()
@logged_tool(SERVER_NAME)
def search_inventory(query: str) -> dict:
    """Search warehouse inventory by SKU or product name keyword.

    Args:
        query: A SKU (e.g. "SKU-1001") or a keyword (e.g. "keyboard").
            Must be non-empty.

    Returns:
        A dict with `query`, `matches` (list of {sku, name, stock} dicts —
        an EMPTY list is a normal, successful result meaning nothing
        matched, not an error), and `count`.

    Raises:
        StructuredToolError: errorCategory "validation", isRetryable False,
            if query is blank. A query that's well-formed but simply
            matches nothing is NOT an error — see Returns above.
    """
    if not query.strip():
        raise StructuredToolError("validation", False, "query must not be empty.")

    query_lower = query.lower()
    matches = [
        {"sku": sku, **item}
        for sku, item in INVENTORY.items()
        if query_lower in sku.lower() or query_lower in item["name"].lower()
    ]
    return {"query": query, "matches": matches, "count": len(matches)}


@mcp.tool()
@logged_tool(SERVER_NAME)
def reserve_stock(sku: str, quantity: int) -> dict:
    """Reserve a quantity of a SKU against current warehouse stock.

    Args:
        sku: Exact SKU, e.g. "SKU-1001".
        quantity: Positive integer number of units to reserve.

    Returns:
        A dict with `sku`, `reserved` (quantity), and `remaining_stock`.

    Raises:
        StructuredToolError: errorCategory "validation", isRetryable False,
            in three cases — unknown SKU, a non-positive quantity, or
            (the business-rule case) requesting more units than are
            currently in stock. All three are non-retryable: retrying the
            identical request will never succeed without the caller
            changing the SKU or quantity.
    """
    item = INVENTORY.get(sku)
    if item is None:
        raise StructuredToolError("validation", False, f"No inventory item found with SKU '{sku}'.")
    if quantity <= 0:
        raise StructuredToolError("validation", False, "quantity must be a positive integer.")
    if quantity > item["stock"]:
        raise StructuredToolError(
            "validation",
            False,
            f"Only {item['stock']} unit(s) of '{item['name']}' ({sku}) are in stock right now — "
            f"you requested {quantity}. Reduce the quantity or check back after the next restock.",
        )

    item["stock"] -= quantity
    return {"sku": sku, "reserved": quantity, "remaining_stock": item["stock"]}


@mcp.tool()
@logged_tool(SERVER_NAME)
def ship_order(order_id: str, approved_by: str = "") -> dict:
    """Ship an order, enforcing manager approval above the value threshold.

    Args:
        order_id: Exact order ID, e.g. "ORDER-500".
        approved_by: A manager ID, e.g. "MGR-001". Only required when the
            order's value exceeds the approval threshold — omit it for
            lower-value orders.

    Returns:
        A dict with `order_id`, `status` ("shipped"), and `approved_by`
        (None if approval wasn't required).

    Raises:
        StructuredToolError: errorCategory "validation" (isRetryable False)
            if order_id is unknown. errorCategory "permission" (isRetryable
            False) if the order's value is above the approval threshold and
            approved_by isn't a recognized manager ID — escalate to a
            supervisor rather than retrying with the same arguments.
    """
    order = ORDERS.get(order_id)
    if order is None:
        raise StructuredToolError("validation", False, f"No order found with ID '{order_id}'.")

    if order["value_usd"] > APPROVAL_THRESHOLD_USD and approved_by not in AUTHORIZED_MANAGERS:
        raise StructuredToolError(
            "permission",
            False,
            f"Order {order_id} is ${order['value_usd']:.2f}, above the ${APPROVAL_THRESHOLD_USD:.2f} "
            "threshold that requires manager approval. Provide a valid manager ID in approved_by, "
            "or escalate to a supervisor for approval.",
        )

    return {"order_id": order_id, "status": "shipped", "approved_by": approved_by or None}


@mcp.tool()
@logged_tool(SERVER_NAME)
def check_carrier_status(order_id: str) -> dict:
    """Check an order's shipment status across every regional carrier mirror.

    Queries each region in turn; a region that times out is retried locally
    a few times before being folded into the result as unresolved, rather
    than failing the whole call over one bad region.

    Args:
        order_id: Exact order ID, e.g. "ORDER-500".

    Returns:
        A dict with `order_id`, `results` (region -> status for every region
        that answered), `partial` (True if at least one region — but not
        every region — was unresolved after local retries), and `unresolved`
        (what was attempted for any region that's still down).

    Raises:
        StructuredToolError: errorCategory "validation" (isRetryable False)
            if order_id is unknown. errorCategory "transient" (isRetryable
            True) only if EVERY region is unresolved after local retries —
            at that point there's no partial result worth returning, and
            retrying the whole call later is the right move.
    """
    if order_id not in ORDERS:
        raise StructuredToolError("validation", False, f"No order found with ID '{order_id}'.")

    flaky_regions = FLAKY_REGIONS_FOR_ORDER.get(order_id, set())
    results = {}
    unresolved = []
    for region in CARRIER_REGIONS:
        if region in flaky_regions:
            unresolved.append(f"{region}: retried 3x locally, still unreachable (simulated timeout)")
        else:
            results[region] = f"in transit via {region}"

    if not results:
        raise StructuredToolError(
            "transient",
            True,
            "All carrier regions are unreachable after local retries; safe to retry this call.",
        )

    return {
        "order_id": order_id,
        "results": results,
        "partial": bool(unresolved),
        "unresolved": unresolved,
    }


if __name__ == "__main__":
    mcp.run()
