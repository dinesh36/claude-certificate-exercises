"""Mock multi-carrier tracking data for the exercise (Domain 1.5).

Each carrier's raw record is deliberately shaped like a different backend
API would actually return it — this is the "heterogeneous data formats
from different MCP tools" that normalize.py's PostToolUse hook exists to
reconcile before the model ever reasons about delivery status.
"""

# FedEx-style: Unix epoch timestamp + a numeric status code.
FEDEX_STATUS_CODES = {
    1: "label_created",
    2: "in_transit",
    3: "out_for_delivery",
    4: "delivered",
    5: "exception",
}
FEDEX_TRACKING = {
    "FDX-1001": {"epoch_ts": 1784107800, "code": 4},  # 2026-07-15T09:30:00Z, delivered
}

# Regional courier: ISO 8601 timestamp + a free-text status string that
# doesn't match our canonical vocabulary casing/wording.
REGIONAL_STATUS_MAP = {
    "Delayed": "exception",
    "Delivered": "delivered",
    "Out For Delivery": "out_for_delivery",
    "In Transit": "in_transit",
}
REGIONAL_TRACKING = {
    "RC-2002": {"timestamp": "2026-07-14T09:15:00Z", "status": "Delayed"},
}

# Legacy carrier: a custom "MM-DD-YYYY HH:MM AM/PM" date string + a
# single-letter status flag.
LEGACY_STATUS_FLAGS = {
    "C": "label_created",
    "T": "in_transit",
    "O": "out_for_delivery",
    "D": "delivered",
    "X": "exception",
}
LEGACY_TRACKING = {
    "LG-3003": {"date_str": "07-13-2026 11:45 AM", "status_flag": "X"},
}

# Shipping-credit ledger: tracking_id -> total amount credited so far.
CREDITS_ISSUED: dict[str, float] = {}
