def apply_percentage_discount(amount_cents: int, percent_off: float) -> int:
    """Apply a percentage discount to a cent amount, clamped to [0, amount]."""
    if percent_off < 0 or percent_off > 100:
        raise ValueError("percent_off must be between 0 and 100")
    discounted = amount_cents * (1 - percent_off / 100)
    return round(discounted)
