"""Minimal illustrative stub for the billing_api package (Task Statement 3.1 sample).

Not a working service — just enough shape for packages/billing_api/CLAUDE.md's
REST conventions (versioned routes, Idempotency-Key, structured error shape) to
have something concrete to point at.
"""


def create_payment_intent(amount_cents: int, idempotency_key: str) -> dict:
    """Would back a POST /v1/payment-intents route in a real service."""
    return {
        "payment_intent_id": "pi_mock_123",
        "amount_cents": amount_cents,
        "status": "requires_confirmation",
    }
