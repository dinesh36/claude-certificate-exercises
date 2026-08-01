"""
Preparation Exercise 1: Multi-Tool Agent with Escalation Logic
Domains reinforced: 1 (Agentic Architecture & Orchestration), 2 (Tool Design & MCP Integration),
5 (Context Management & Reliability)

A release-engineering agent with four tools (two of them deliberately
similar — get_deployment_status vs. list_deployments — to test
tool-selection accuracy), structured tool error responses, a programmatic
hook that blocks high-risk production deploys and redirects to on-call
escalation, and a manual agentic loop that terminates strictly on
stop_reason.

See tools.py for the tool schemas/implementations, policy.py for the
production risk-threshold hook, and data.py for the mock deployment store.
"""

import sys

from common.agent_loop import run_tool_loop
from common.client import DEFAULT_MODEL, get_client

from policy import enforce_deploy_risk_policy
from tools import TOOLS

client = get_client()

SYSTEM_PROMPT = (
    "You are a release-engineering assistant managing deployments for a software company. "
    "Decompose multi-part requests into distinct concerns and address each one. "
    "Use get_deployment_status only when you have an exact deployment ID; use "
    "list_deployments when you don't. If a production deploy is blocked by policy, "
    "escalate to the on-call lead with a structured handoff summary rather than "
    "retrying request_deploy. Retry tool calls that report a transient, retryable "
    "error; do not retry validation or permission errors — explain those instead."
)


if __name__ == "__main__":
    scenario = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "Please deploy version 4.2.0 of payments-service to production with a risk score "
            "of 9. Also, can you check what deployments checkout-api currently has running in "
            "staging?"
        )
    )
    print(f"User: {scenario}\n")
    result = run_tool_loop(
        client=client,
        model=DEFAULT_MODEL,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        user_message=scenario,
        pre_hook=enforce_deploy_risk_policy,
    )
    print(f"\nAgent: {result.final_text}")
