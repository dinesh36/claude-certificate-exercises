"""
Exercise 3: Subagent Invocation & Context Passing
Domain: 1 (Agentic Architecture & Orchestration) — Task Statement 1.3

A trip-planning coordinator that reviews a small set of travel blog excerpts
about one destination by dispatching one isolated review subagent per post
(emitted together in a single turn), passes the COMPLETE structured
findings directly into a synthesis subagent, then forks that shared
destination-summary baseline into two divergent itinerary subagents (budget
vs. luxury) called in parallel from the identical baseline text.

See data.py for the mock blog posts and tools.py for the three
subagent-dispatch tools, their AgentDefinition-like configuration, and each
subagent call (isolated via common/subagent.py).
"""

import sys

from common.agent_loop import run_tool_loop
from common.client import DEFAULT_MODEL, get_client

from data import BLOG_POSTS
from tools import TOOLS, build_dispatcher

client = get_client()

SYSTEM_PROMPT = (
    "You are a trip-planning coordinator helping someone plan a trip to "
    f"Lisbon, Portugal. Known blog posts: {', '.join(BLOG_POSTS)}. All blog "
    "review, synthesis, and itinerary work is delegated to subagents via "
    "dispatch_blog_review_subagent, dispatch_synthesis_subagent, and "
    "dispatch_itinerary_subagent — you never read or judge the blog posts yourself.\n\n"
    "First, review every blog post relevant to the question asked: call "
    "dispatch_blog_review_subagent once per relevant post, emitting all of "
    "those calls together in this same turn rather than one at a time across "
    "separate turns. Then pass the complete findings (not just IDs or "
    "summaries) to dispatch_synthesis_subagent with a focus describing what "
    "the summary should resolve.\n\n"
    "Only if the user wants a specific itinerary, fork the synthesis into "
    "two divergent explorations by calling dispatch_itinerary_subagent twice "
    "in the same turn — once with style='budget' and once with style='luxury' "
    "— passing the exact same baseline_summary text to both. Finish with a "
    "response addressing exactly what the user asked, no more and no less."
)


if __name__ == "__main__":
    scenario = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "I'm planning a trip to Lisbon. Pull together what these blog posts say "
            "about it, and give me both a budget and a luxury itinerary option."
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
        # The coordinator must repeat the full destination summary as tool
        # input for BOTH forked dispatch_itinerary_subagent calls in the same
        # turn (Task Statement 1.3's "complete findings passed directly"),
        # which is large enough to need more headroom than the loop's default.
        max_tokens=8192,
    )
    print(f"\nAgent: {result.final_text}")
