"""Synchronous calls to the mock payment gateway."""


class PaymentDeclinedError(Exception):
    pass


def charge(amount: float, card_token: str) -> str:
    """Synchronously charge a card and return a transaction ID.

    In production this blocks on a network call to the payment gateway.
    """
    if amount <= 0:
        raise ValueError("Charge amount must be positive.")
    if card_token == "declined":
        raise PaymentDeclinedError("Card was declined.")
    return f"txn_{card_token}_{int(amount * 100)}"
