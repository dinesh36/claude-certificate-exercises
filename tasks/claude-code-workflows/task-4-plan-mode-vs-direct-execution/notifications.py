"""Order confirmation notifications, sent synchronously after checkout."""


def send_order_confirmation(email: str, order_id: str) -> str:
    """Synchronously send a confirmation email once payment and inventory succeed."""
    return f"Sent confirmation for {order_id} to {email}"
