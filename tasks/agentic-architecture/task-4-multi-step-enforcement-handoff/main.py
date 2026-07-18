"""
Task 4: Multi-Step Enforcement & Handoff
Domain: 1 (Agentic Architecture & Orchestration) — Task Statement 1.4

An IT-helpdesk agent split across `data.py` (mock employee/approval
records), `tools.py` (tool schemas and implementations), `policy.py` (a
programmatic hook that blocks grant_access until a prerequisite approval
check has actually succeeded, and always escalates restricted-tier
systems), and `main.py` (system prompt + entry point), with the reusable
agentic loop factored out into common/agent_loop.py.
"""

import sys

from common.agent_loop import run_tool_loop
from common.client import DEFAULT_MODEL, get_client

from policy import enforce_access_prerequisite
from tools import TOOLS

client = get_client()

SYSTEM_PROMPT = (
    "You are an IT helpdesk agent handling employee system-access requests. "
    "Decompose multi-part requests into distinct concerns and address each one. "
    "Before ever calling grant_access for a system, first call "
    "verify_manager_approval for that exact employee and system — grant_access "
    "will be blocked by policy if you skip this or if approval isn't on file, "
    "and blocked entirely for restricted-tier systems no matter what. "
    "If grant_access is blocked, or verify_manager_approval reports no "
    "approval on file, do not retry grant_access — escalate to "
    "escalate_to_security_team with a structured handoff instead. "
    "Use check_access_level freely to answer questions about existing access."
)


if __name__ == "__main__":
    scenario = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "Hi, I'm Alex Kim (EMP-1). I need access to the shared-drive system, and separately, "
            "can you tell me what access I currently have?"
        )
    )
    print(f"User: {scenario}\n")
    result = run_tool_loop(
        client=client,
        model=DEFAULT_MODEL,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        user_message=scenario,
        pre_hook=enforce_access_prerequisite,
    )
    print(f"\nAgent: {result.final_text}")
