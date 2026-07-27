"""Discount code validation and application."""

_VALID_CODES = {"SAVE10": 0.10, "SAVE20": 0.20}


def validate_code(code: str) -> bool:
    return code in _VALID_CODES


def apply_discount(subtotal: float, code: str) -> float:
    if not validate_code(code):
        return subtotal
    return subtotal * (1 - _VALID_CODES[code])
