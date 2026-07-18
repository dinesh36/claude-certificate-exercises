"""Mock IT-helpdesk directory for the task (Domain 1.4).

Employees carry their current access list; SYSTEM_TIERS marks which systems
are "restricted" (policy.py's hook always escalates these, no matter what);
APPROVALS is the pre-existing manager sign-off record that
verify_manager_approval in tools.py reads from — a missing entry means "no
approval on file yet," not an error.
"""

EMPLOYEES = {
    "EMP-1": {"name": "Alex Kim", "department": "Engineering", "current_access": ["vpn"]},
    "EMP-2": {"name": "Jamie Lopez", "department": "Sales", "current_access": []},
}

SYSTEM_TIERS = {
    "vpn": "standard",
    "shared-drive": "standard",
    "salesforce": "standard",
    "prod-admin": "restricted",
    "payroll-admin": "restricted",
}

# (employee_id, system) -> whether a manager has signed off. EMP-1 is
# approved for both shared-drive (standard) and prod-admin (restricted) —
# the restricted one exists to prove the tier check overrides an existing
# approval rather than only mattering when approval is missing.
APPROVALS = {
    ("EMP-1", "shared-drive"): True,
    ("EMP-1", "prod-admin"): True,
    ("EMP-2", "salesforce"): False,
}

# Populated by tools.py's _verify_manager_approval whenever it reports
# approved=True; read by policy.py's enforce_access_prerequisite hook before
# letting grant_access run — a deterministic record of what was actually
# verified this run, not something the model can just assert happened.
verified_approvals: set[tuple[str, str]] = set()
