"""
Exercise 5: Coordinator-Subagent Orchestration
Domain: 1 (Agentic Architecture & Orchestration) — Task Statement 1.2

A single coordinator loop (the reusable common/agent_loop.py tool-use loop,
reused here one level up as the coordinator's own loop) that dynamically
decides which topic tags a research question actually needs, dispatches
isolated search/analysis subagents per tag through tools.py, and iteratively
re-delegates on partial coverage before producing one unified synthesis —
rather than always running a fixed pipeline across every known topic.

See data.py for the mock research corpus and tools.py for the subagent
dispatch tools (each subagent call is a fresh, isolated Anthropic request —
see common/subagent.py).
"""

import sys

from common.agent_loop import run_tool_loop
from common.client import DEFAULT_MODEL, get_client

from data import TOPIC_TAGS
from tools import TOOLS, build_dispatcher

client = get_client()

SYSTEM_PROMPT = (
    "You are a research coordinator studying remote work's impact on software "
    "engineering teams. All research is delegated to subagents via "
    "dispatch_search_subagent and dispatch_analysis_subagent — you never "
    f"answer from your own general knowledge. Available topic tags: {', '.join(TOPIC_TAGS)}.\n\n"
    "Read the user's question and decide which tags are actually relevant to "
    "it: for a narrow question, dispatch only the one or two tags that "
    "matter; for a broad question, cover enough distinct tags that no major "
    "angle is left out. Assign each subagent a single, non-overlapping tag "
    "so no two subagents research the same ground.\n\n"
    "Every dispatch_search_subagent call without deep_dive=true returns "
    "partial: true and a gap_hint. Before finalizing, decide per tag whether "
    "that gap matters enough to the user's question to re-dispatch with "
    "deep_dive=true — do not synthesize a tag's findings from partial "
    "coverage alone if that tag is central to the question. Use "
    "dispatch_analysis_subagent to distill findings once you have "
    "non-partial coverage worth analyzing, then write the final unified "
    "synthesis yourself, noting which tags you covered and why.\n\n"
    "If a dispatch call returns a transient, retryable error, retry that "
    "exact same call once before treating the topic as unavailable."
)


if __name__ == "__main__":
    scenario = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "We're deciding whether to keep our engineering org remote-first long "
            "term. Give me a broad picture of the impact so far."
        )
    )
    print(f"User: {scenario}\n")
    result = run_tool_loop(
        client=client,
        model=DEFAULT_MODEL,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        dispatcher=build_dispatcher(client, DEFAULT_MODEL),
        user_message=scenario,
    )
    print(f"\nAgent: {result.final_text}")
