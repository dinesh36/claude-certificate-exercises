"""Tool schemas and implementations for the IT access helpdesk (Domain 1.4).

_verify_manager_approval is the prerequisite step; _grant_access is the
sensitive action that policy.py's hook blocks until _verify_manager_approval
has actually confirmed approval for that exact (employee_id, system) pair —
tracked in data.py's verified_approvals, not just trusted from the order the
model happens to call tools in.

The only export is TOOLS: a list of {"schema": ..., "implementation": ...}
entries. common/agent_loop.py extracts the schemas for the Anthropic API call
and builds its own name -> implementation map to dispatch tool_use blocks
directly — nothing else in this module needs to be imported elsewhere.
"""

from common.errors import tool_error

from data import APPROVALS, EMPLOYEES, SYSTEM_TIERS, verified_approvals


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _verify_manager_approval(employee_id: str, system: str) -> dict:
    if employee_id not in EMPLOYEES:
        return tool_error("validation", False, f"No employee found with ID '{employee_id}'.")
    if system not in SYSTEM_TIERS:
        return tool_error(
            "validation", False, f"Unknown system '{system}'. Valid systems: {', '.join(SYSTEM_TIERS)}."
        )

    approved = APPROVALS.get((employee_id, system), False)
    if approved:
        verified_approvals.add((employee_id, system))
    return {
        "employee_id": employee_id,
        "system": system,
        "approved": approved,
        "reason": "Manager approval on file." if approved else "No manager approval on file for this system.",
    }


def _check_access_level(employee_id: str) -> dict:
    employee = EMPLOYEES.get(employee_id)
    if employee is None:
        return tool_error("validation", False, f"No employee found with ID '{employee_id}'.")
    return {"employee_id": employee_id, "current_access": list(employee["current_access"])}


def _grant_access(employee_id: str, system: str) -> dict:
    # Only reachable if policy.py's hook let it through — see enforce_access_prerequisite.
    employee = EMPLOYEES.get(employee_id)
    if employee is None:
        return tool_error("validation", False, f"No employee found with ID '{employee_id}'.")
    if system not in employee["current_access"]:
        employee["current_access"].append(system)
    return {"employee_id": employee_id, "system": system, "status": "access_granted"}


def _escalate_to_security_team(
    employee_id: str, issue_summary: str, root_cause: str, recommended_action: str, system: str = ""
) -> dict:
    ticket_id = f"SEC-{abs(hash((employee_id, issue_summary))) % 100000:05d}"
    return {
        "ticket_id": ticket_id,
        "employee_id": employee_id,
        "system": system or None,
        "issue_summary": issue_summary,
        "root_cause": root_cause,
        "recommended_action": recommended_action,
        "status": "escalated_to_security_team",
    }


# ---------------------------------------------------------------------------
# TOOLS — the only export: one {schema, implementation} entry per tool
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "schema": {
            "name": "verify_manager_approval",
            "description": (
                "Check whether an employee's manager has signed off on access to a specific system. "
                "This is the required prerequisite step — grant_access will be blocked until this has "
                "been called for the same employee_id and system and has reported approved: true. "
                "A false result is not an error; it means escalate instead of granting."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string", "description": "Exact employee ID, e.g. 'EMP-1'."},
                    "system": {"type": "string", "description": "Exact system name, e.g. 'shared-drive'."},
                },
                "required": ["employee_id", "system"],
            },
        },
        "implementation": _verify_manager_approval,
    },
    {
        "schema": {
            "name": "check_access_level",
            "description": (
                "Look up which systems an employee currently has access to. Freely callable at any "
                "time — this is a read-only lookup, not gated by any prerequisite."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string", "description": "Exact employee ID, e.g. 'EMP-1'."},
                },
                "required": ["employee_id"],
            },
        },
        "implementation": _check_access_level,
    },
    {
        "schema": {
            "name": "grant_access",
            "description": (
                "Grant an employee access to a system. Blocked by policy until verify_manager_approval "
                "has confirmed approval for this exact employee_id and system, and blocked entirely for "
                "restricted-tier systems regardless of approval — do not retry this call after it's "
                "blocked; escalate to escalate_to_security_team instead."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string", "description": "Exact employee ID to grant access to."},
                    "system": {"type": "string", "description": "Exact system name to grant."},
                },
                "required": ["employee_id", "system"],
            },
        },
        "implementation": _grant_access,
    },
    {
        "schema": {
            "name": "escalate_to_security_team",
            "description": (
                "Hand off the request to a human security-team member. Use this when grant_access is "
                "blocked by policy (no approval on file, or a restricted-tier system), or when the "
                "issue can't be resolved with the available tools. Produces a structured summary (root "
                "cause, recommended action) since the human has no access to this conversation transcript."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string"},
                    "system": {"type": "string", "description": "Related system, if any."},
                    "issue_summary": {"type": "string", "description": "One-paragraph summary of the request."},
                    "root_cause": {"type": "string", "description": "Why this couldn't be resolved automatically."},
                    "recommended_action": {"type": "string", "description": "What the security team should do next."},
                },
                "required": ["employee_id", "issue_summary", "root_cause", "recommended_action"],
            },
        },
        "implementation": _escalate_to_security_team,
    },
]
