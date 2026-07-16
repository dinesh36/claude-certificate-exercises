"""Tool schemas and implementations for the coordinator (Domain 1.2).

Both tools dispatch to an isolated subagent call (common.subagent.run_subagent)
rather than answering directly. The subagent only ever sees what this module
explicitly forwards to it in `user_message` — never the coordinator's
conversation history, the original user question, or another subagent's
output — which is what demonstrates isolated subagent context in code rather
than just asserting it in the prompt.
"""

from common.errors import tool_error
from common.subagent import run_subagent

from data import FLAKY_TOPIC_TAG, KNOWLEDGE_BASE, TOPIC_TAGS, _flaky_attempts

SEARCH_SUBAGENT_SYSTEM = (
    "You are a research search subagent. You have no knowledge of the "
    "original user request, the coordinator's plan, or any other subagent's "
    "output — you only know the topic and source snippets given below. "
    "Summarize the key findings from ONLY those snippets in 2-3 sentences."
)

ANALYSIS_SUBAGENT_SYSTEM = (
    "You are a research analysis subagent. You have no knowledge of the "
    "original user request or the coordinator's overall plan — you only "
    "know the topic summaries explicitly given to you below. Synthesize "
    "them into a short, focused analysis addressing the stated focus."
)

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _dispatch_search_subagent(client, model: str, topic_tag: str, deep_dive: bool = False) -> dict:
    if topic_tag not in KNOWLEDGE_BASE:
        return tool_error(
            "validation",
            False,
            f"Unknown topic_tag '{topic_tag}'. Valid tags: {', '.join(TOPIC_TAGS)}.",
        )

    if topic_tag == FLAKY_TOPIC_TAG:
        attempts = _flaky_attempts.get(topic_tag, 0)
        _flaky_attempts[topic_tag] = attempts + 1
        if attempts == 0:
            raise RuntimeError(f"simulated subagent network timeout while searching '{topic_tag}'")

    snippets = KNOWLEDGE_BASE[topic_tag]
    visible = snippets if deep_dive else snippets[:1]

    user_message = f"Topic: {topic_tag}\n\nSource snippets:\n" + "\n".join(f"- {s}" for s in visible)
    summary = run_subagent(client, model, SEARCH_SUBAGENT_SYSTEM, user_message)

    result = {"topic_tag": topic_tag, "summary": summary, "partial": not deep_dive}
    if not deep_dive:
        result["gap_hint"] = (
            f"Only {len(visible)} of {len(snippets)} known sources on '{topic_tag}' were searched. "
            "Call again with deep_dive=true if this topic is central to the user's question."
        )
    return result


def _dispatch_analysis_subagent(client, model: str, topic_tag: str, summaries: list[str], focus: str) -> dict:
    if not summaries:
        return tool_error(
            "validation",
            False,
            "summaries must contain at least one prior search-subagent summary to analyze.",
        )

    joined = "\n".join(f"- {s}" for s in summaries)
    user_message = f"Topic: {topic_tag}\nFocus: {focus}\n\nSummaries to synthesize:\n{joined}"
    analysis = run_subagent(client, model, ANALYSIS_SUBAGENT_SYSTEM, user_message)
    return {"topic_tag": topic_tag, "focus": focus, "analysis": analysis}


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "dispatch_search_subagent",
        "description": (
            "Delegate research on ONE topic tag to an isolated search subagent. The "
            "subagent sees only the tag and matching source snippets — never the "
            "user's original question or any other subagent's output. Call this once "
            "per distinct topic_tag you decide is relevant; do not call it for every "
            "available tag on a narrow question, and do not skip relevant tags on a "
            "broad one. Each call returns `partial: true` and a `gap_hint` unless "
            "deep_dive is set — check both before deciding whether to re-delegate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic_tag": {
                    "type": "string",
                    "enum": TOPIC_TAGS,
                    "description": "The single topic to research in this call.",
                },
                "deep_dive": {
                    "type": "boolean",
                    "description": "Set true to retrieve full source coverage for this tag after a prior partial call revealed a gap worth closing.",
                },
            },
            "required": ["topic_tag"],
        },
    },
    {
        "name": "dispatch_analysis_subagent",
        "description": (
            "Delegate synthesis of ALREADY-GATHERED search-subagent summaries to an "
            "isolated analysis subagent. You must pass the summaries explicitly — "
            "the subagent does not have access to prior dispatch_search_subagent "
            "results on its own. Use this to distill findings for one topic once you "
            "have non-partial coverage worth analyzing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic_tag": {"type": "string", "description": "The topic these summaries are about."},
                "summaries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The prior dispatch_search_subagent summary text(s) to synthesize.",
                },
                "focus": {"type": "string", "description": "What the analysis should focus on for the user's question."},
            },
            "required": ["topic_tag", "summaries", "focus"],
        },
    },
]


def build_dispatcher(client, model: str):
    """Bind the coordinator's Anthropic client/model into a ToolDispatcher closure."""

    def dispatch_tool(tool_name: str, tool_input: dict) -> dict:
        if tool_name == "dispatch_search_subagent":
            return _dispatch_search_subagent(client, model, **tool_input)
        if tool_name == "dispatch_analysis_subagent":
            return _dispatch_analysis_subagent(client, model, **tool_input)
        return tool_error("validation", False, f"Unknown tool '{tool_name}'.")

    return dispatch_tool
