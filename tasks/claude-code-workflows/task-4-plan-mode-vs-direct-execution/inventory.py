"""Synchronous stock reservation and deduction."""

_STOCK = {"WIDGET-1": 50, "WIDGET-2": 5}


class OutOfStockError(Exception):
    pass


def reserve_stock(sku: str, quantity: int) -> None:
    """Synchronously reserve stock for an order, blocking the caller until it completes."""
    if _STOCK.get(sku, 0) < quantity:
        raise OutOfStockError(f"Not enough stock for {sku}.")
    _STOCK[sku] -= quantity
