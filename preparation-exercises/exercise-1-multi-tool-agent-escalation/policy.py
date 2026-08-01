"""Programmatic policy hook (Domain 1.5).

Intercepts request_deploy calls BEFORE execution and enforces the
production risk-threshold business rule deterministically, rather than
relying on the model to remember and honor a prompt instruction.
"""

from common.errors import tool_error

PRODUCTION_RISK_THRESHOLD = 7


def enforce_deploy_risk_policy(tool_name: str, tool_input: dict) -> dict | None:
    if tool_name != "request_deploy":
        return None
    if tool_input.get("environment") != "production":
        return None
    risk_score = tool_input.get("risk_score")
    if isinstance(risk_score, (int, float)) and risk_score > PRODUCTION_RISK_THRESHOLD:
        return tool_error(
            "permission",
            False,
            (
                f"Risk score {risk_score} exceeds the production threshold of "
                f"{PRODUCTION_RISK_THRESHOLD}. Blocked by policy hook — escalate to the on-call "
                "lead via escalate_to_oncall instead of retrying request_deploy."
            ),
        )
    return None
