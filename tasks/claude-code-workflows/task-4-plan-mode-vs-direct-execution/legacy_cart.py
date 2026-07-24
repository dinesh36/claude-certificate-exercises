"""Deprecated: use cart.Cart instead. Kept only for two call sites that haven't migrated yet."""


class LegacyCart:
    """Deprecated pre-refactor cart representation. Do not use in new code."""

    def __init__(self, line_items: list[tuple[str, float, int]]):
        self.line_items = line_items

    def total(self) -> float:
        return sum(price * qty for _, price, qty in self.line_items)
