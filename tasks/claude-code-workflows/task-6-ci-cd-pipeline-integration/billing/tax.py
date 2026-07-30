_TAX_RATES_BPS = {
    "CA": 725,
    "NY": 800,
    "OR": 0,
}


def calculate_tax(amount_cents: int, region: str) -> int:
    """Return tax owed, in cents, for a cent amount in a given US state region."""
    if region not in _TAX_RATES_BPS:
        raise ValueError(f"unknown tax region: {region}")
    return round(amount_cents * _TAX_RATES_BPS[region] / 10000)
