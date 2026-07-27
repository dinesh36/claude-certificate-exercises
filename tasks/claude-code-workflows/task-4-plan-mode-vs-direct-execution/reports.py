"""Legacy order-total reporting. Still depends on LegacyCart for one code path."""

from legacy_cart import LegacyCart


def legacy_order_total(line_items: list[tuple[str, float, int]]) -> float:
    """Compute a total the old way, for orders imported from the pre-refactor system."""
    return LegacyCart(line_items).total()
