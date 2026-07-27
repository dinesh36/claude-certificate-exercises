"""Checkout orchestration: cart -> payment -> inventory -> notification, all synchronous."""

from cart import Cart
from discounts import apply_discount
from inventory import reserve_stock
from notifications import send_order_confirmation
from payment_processor import charge


def checkout(cart: Cart, card_token: str, email: str, discount_code: str | None = None) -> dict:
    """Run the full checkout flow, blocking on each step in turn.

    Every step below is a synchronous call: the payment gateway charge, the
    inventory reservation, and the confirmation email each block the request
    until they finish, one after another.
    """
    subtotal = cart.subtotal()
    total = apply_discount(subtotal, discount_code) if discount_code else subtotal

    transaction_id = charge(total, card_token)

    for item in cart.items:
        reserve_stock(item["sku"], item["quantity"])

    send_order_confirmation(email, transaction_id)

    return {"transaction_id": transaction_id, "total": total}
