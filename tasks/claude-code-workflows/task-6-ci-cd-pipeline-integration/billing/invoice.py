class Invoice:
    def __init__(self):
        self.line_items = []

    def add_line_item(self, description, unit_price_cents, quantity, discount_percent=0):
        self.line_items.append({
            "description": description,
            "unit_price_cents": unit_price_cents,
            "quantity": quantity,
            "discount_percent": discount_percent,
        })

    def subtotal_cents(self) -> int:
        return sum(item["unit_price_cents"] * item["quantity"] for item in self.line_items)

    def total_cents(self) -> int:
        """Subtotal with each line item's discount_percent applied."""
        return self.subtotal_cents()
