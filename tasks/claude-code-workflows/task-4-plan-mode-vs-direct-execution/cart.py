"""Shopping cart: add/remove items and compute totals."""


class Cart:
    def __init__(self):
        self.items = []

    def add_item(self, sku: str, price: float, quantity: int = 1) -> None:
        self.items.append({"sku": sku, "price": price, "quantity": quantity})

    def remove_item(self, sku: str) -> None:
        self.items = [item for item in self.items if item["sku"] != sku]

    def subtotal(self) -> float:
        return sum(item["price"] * item["quantity"] for item in self.items)
