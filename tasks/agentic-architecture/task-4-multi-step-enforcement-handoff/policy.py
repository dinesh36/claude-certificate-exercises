"""Programmatic prerequisite-gate hook (Domain 1.4).

Blocks grant_access deterministically — both for missing manager
verification and for restricted-tier systems — rather than trusting the
model's prompt-following to check these before calling grant_access.
"""

from common.errors import tool_error

from data import SYSTEM_TIERS, verified_approvals


def enforce_access_prerequisite(tool_name: str, tool_input: dict) -> dict | None:
    if tool_name != "grant_access":
        return None

    employee_id = tool_input.get("employee_id")
    system = tool_input.get("system")

    if SYSTEM_TIERS.get(system) == "restricted":
        return tool_error(
            "permission",
            False,
            f"'{system}' is a restricted-tier system — it always requires human security-team "
            "sign-off and can never be auto-granted, even with manager approval on file. "
            "Escalate to escalate_to_security_team instead of retrying grant_access.",
        )

    if (employee_id, system) not in verified_approvals:
        return tool_error(
            "permission",
            False,
            f"grant_access is blocked: verify_manager_approval has not confirmed approval for "
            f"'{employee_id}' on '{system}'. Call verify_manager_approval first; if it comes back "
            "unapproved, escalate to escalate_to_security_team instead of retrying grant_access.",
        )

    return None
