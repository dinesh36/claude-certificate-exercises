"""PostToolUse data-normalization hook (Domain 1.5).

Each carrier tool in tools.py returns its own raw shape — a Unix epoch +
numeric code, an ISO 8601 timestamp + free-text status, or a custom date
string + single-letter flag. normalize_carrier_result runs after dispatch
(wired in via common/agent_loop.py's post_hook) and rewrites every one of
them into the same {tracking_id, carrier, status, last_update} shape before
the model ever reasons about delivery status — the model never has to
parse three different timestamp/status formats itself.
"""

from datetime import datetime, timezone

from data import FEDEX_STATUS_CODES, LEGACY_STATUS_FLAGS, REGIONAL_STATUS_MAP

CARRIER_NAMES = {
    "check_fedex_status": "FedEx-style Express",
    "check_regional_courier_status": "Regional Courier Co.",
    "check_legacy_carrier_status": "Legacy Freight Lines",
}


def normalize_carrier_result(tool_name: str, tool_input: dict, result: dict) -> dict:
    if tool_name not in CARRIER_NAMES:
        return result  # not a carrier lookup — pass through unchanged

    if tool_name == "check_fedex_status":
        last_update = datetime.fromtimestamp(result["epoch_ts"], tz=timezone.utc).isoformat()
        status = FEDEX_STATUS_CODES.get(result["code"], "unknown")
    elif tool_name == "check_regional_courier_status":
        last_update = result["timestamp"]
        status = REGIONAL_STATUS_MAP.get(result["status"], result["status"].lower().replace(" ", "_"))
    else:  # check_legacy_carrier_status
        parsed = datetime.strptime(result["date_str"], "%m-%d-%Y %I:%M %p").replace(tzinfo=timezone.utc)
        last_update = parsed.isoformat()
        status = LEGACY_STATUS_FLAGS.get(result["status_flag"], "unknown")

    return {
        "tracking_id": result["tracking_id"],
        "carrier": CARRIER_NAMES[tool_name],
        "status": status,
        "last_update": last_update,
    }
