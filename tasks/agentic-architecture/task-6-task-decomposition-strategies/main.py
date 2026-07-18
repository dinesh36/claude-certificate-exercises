"""
Task 6: Task Decomposition Strategies
Domain: 1 (Agentic Architecture & Orchestration) — Task Statement 1.6

A manufacturing quality-control coordinator that picks the decomposition
strategy to fit the request: a fixed prompt-chaining pipeline
(inspect_batch per named batch, then one cross-batch integration pass) for
predictable multi-batch reviews, versus dynamic adaptive decomposition
(scope_customer_defect_report first, then investigate_root_cause only for
whichever areas the scope actually flags) for open-ended customer-defect
investigations where the right follow-up isn't known upfront.

See data.py for the mock batch/defect-report data and tools.py for the four
tool schemas/implementations.
"""

import sys

from common.agent_loop import run_tool_loop
from common.client import DEFAULT_MODEL, get_client

from tools import TOOLS

client = get_client()

SYSTEM_PROMPT = (
    "You are a manufacturing quality-control coordinator. Pick the "
    "decomposition strategy that fits the request:\n\n"
    "If the user names specific batch IDs to review, use the FIXED "
    "pipeline: call inspect_batch once per named batch, emitting all of "
    "those calls together in this same turn, then once you have every "
    "batch's findings, call run_cross_batch_defect_trend with the complete "
    "findings to look for a cross-batch pattern.\n\n"
    "If the user describes an open-ended customer-reported defect on a "
    "product (no batch IDs given), use the DYNAMIC path instead: call "
    "scope_customer_defect_report first to see which root-cause areas "
    "actually look suspicious, then call investigate_root_cause only for "
    "the areas that came back flagged — never investigate an area the "
    "scope didn't flag, and never skip one it did. Do not blend the two "
    "patterns for a single request; pick the one that fits, then write a "
    "unified conclusion."
)


if __name__ == "__main__":
    scenario = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "Can you review production batches BATCH-101, BATCH-102, and BATCH-103 from "
            "today's runs and tell me if there's a pattern?"
        )
    )
    print(f"User: {scenario}\n")
    result = run_tool_loop(
        client=client,
        model=DEFAULT_MODEL,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        user_message=scenario,
    )
    print(f"\nAgent: {result.final_text}")
