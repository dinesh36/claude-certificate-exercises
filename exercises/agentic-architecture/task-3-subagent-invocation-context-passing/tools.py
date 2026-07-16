"""Tool schemas and implementations for the coordinator (Domain 1.3).

Three subagent types, each configured as an AgentDefinition-like entry in
SUBAGENT_DEFINITIONS (description + system prompt + tool restrictions) per
Task Statement 1.3's "AgentDefinition configuration... for each subagent
type." Every call is an isolated single-turn subagent invocation
(common.subagent.run_subagent) that receives only what this module
explicitly puts in its user_message — never the coordinator's own history
or another subagent's raw output.
"""

from common.errors import tool_error
from common.subagent import run_subagent

from data import BLOG_POSTS

BLOG_REVIEW_SYSTEM = (
    "You are a travel-blog review subagent. You have no knowledge of the "
    "trip-planning request, the other blog posts, or the coordinator's plan "
    "— you only see the single blog excerpt given below. Extract ONE claim "
    "(one sentence, what this excerpt recommends or establishes) and copy "
    "the single most relevant sentence as a verbatim evidence excerpt. "
    "Respond as exactly two lines: 'Claim: ...' then 'Evidence: ...'."
)

SYNTHESIS_SYSTEM = (
    "You are a travel-synthesis subagent. You have no knowledge of the "
    "coordinator's plan or the original blog posts — you only know the "
    "findings explicitly given to you below, each with its claim, evidence, "
    "and source citation. Write a short destination summary addressing the "
    "stated focus, citing each fact inline as (BlogName, Author) using only "
    "the citations given — never invent a source."
)

ITINERARY_SYSTEM = (
    "You are a trip-itinerary subagent exploring ONE travel style for a "
    "destination. You have no knowledge of any other style being explored "
    "in parallel — you only know the shared destination summary given below "
    "and the style you've been assigned. Recommend a simple 2-3 day "
    "itinerary consistent with that style, grounded only in the summary given."
)

# AgentDefinition-like configuration per subagent type (Task Statement 1.3's
# "descriptions, system prompts, and tool restrictions for each subagent
# type"). Every subagent here is a single-turn, tool-free call (see
# common/subagent.py), so allowed_tools is empty for all three.
SUBAGENT_DEFINITIONS = {
    "blog_review": {
        "description": "Extracts one structured claim+evidence finding from a single travel blog post, isolated from the rest of the trip research.",
        "system_prompt": BLOG_REVIEW_SYSTEM,
        "allowed_tools": [],
    },
    "synthesis": {
        "description": "Synthesizes multiple prior findings (with full attribution) into a short destination summary.",
        "system_prompt": SYNTHESIS_SYSTEM,
        "allowed_tools": [],
    },
    "itinerary": {
        "description": "Explores one recommended travel style (budget/luxury) forked from a shared destination-summary baseline.",
        "system_prompt": ITINERARY_SYSTEM,
        "allowed_tools": [],
    },
}


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _parse_claim_evidence(text: str) -> tuple[str, str]:
    claim, evidence = "", ""
    for line in text.splitlines():
        if line.lower().startswith("claim:"):
            claim = line.split(":", 1)[1].strip()
        elif line.lower().startswith("evidence:"):
            evidence = line.split(":", 1)[1].strip()
    return claim or text.strip(), evidence


def _dispatch_blog_review_subagent(client, model: str, post_id: str) -> dict:
    post = BLOG_POSTS.get(post_id)
    if post is None:
        return tool_error(
            "validation",
            False,
            f"No blog post found with ID '{post_id}'. Valid IDs: {', '.join(BLOG_POSTS)}.",
        )

    user_message = f"Blog excerpt:\n{post['text']}"
    raw = run_subagent(client, model, SUBAGENT_DEFINITIONS["blog_review"]["system_prompt"], user_message)
    claim, evidence = _parse_claim_evidence(raw)

    return {
        "post_id": post_id,
        "claim": claim,
        "evidence_excerpt": evidence,
        "source": {"blog_name": post["blog_name"], "author": post["author"]},
    }


def _dispatch_synthesis_subagent(client, model: str, findings: list[dict], focus: str) -> dict:
    if not findings:
        return tool_error(
            "validation",
            False,
            "findings must contain at least one prior dispatch_blog_review_subagent result to synthesize.",
        )

    joined = "\n".join(
        f"- Claim: {f['claim']}\n"
        f"  Evidence: {f['evidence_excerpt']}\n"
        f"  Source: ({f['source']['blog_name']}, {f['source']['author']})"
        for f in findings
    )
    user_message = f"Focus: {focus}\n\nFindings to synthesize:\n{joined}"
    # A full destination summary runs longer than common/subagent.py's
    # 1024-token default (which truncated the summary mid-sentence in testing).
    summary = run_subagent(client, model, SUBAGENT_DEFINITIONS["synthesis"]["system_prompt"], user_message, max_tokens=2048)
    return {"focus": focus, "summary": summary}


def _dispatch_itinerary_subagent(client, model: str, baseline_summary: str, style: str) -> dict:
    if style not in ("budget", "luxury"):
        return tool_error(
            "validation",
            False,
            f"style must be 'budget' or 'luxury', got '{style}'.",
        )

    user_message = f"Destination summary (shared baseline):\n{baseline_summary}\n\nYour assigned style: {style}"
    itinerary = run_subagent(client, model, SUBAGENT_DEFINITIONS["itinerary"]["system_prompt"], user_message)
    return {"style": style, "itinerary": itinerary}


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "dispatch_blog_review_subagent",
        "description": (
            "Delegate review of ONE travel blog post to an isolated review subagent, "
            "which returns a structured finding: a claim, a verbatim evidence excerpt, "
            "and a source citation (blog_name + author) kept separate from the content. "
            "Call this once per post you need reviewed; to review several posts, emit "
            "all the calls you need together in this same turn rather than one at a "
            "time across separate turns."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "post_id": {
                    "type": "string",
                    "enum": list(BLOG_POSTS),
                    "description": "Exact blog post ID to review.",
                },
            },
            "required": ["post_id"],
        },
    },
    {
        "name": "dispatch_synthesis_subagent",
        "description": (
            "Delegate synthesis to an isolated subagent. You must pass the COMPLETE prior "
            "findings (claim, evidence_excerpt, and source for each) directly as `findings` "
            "— the subagent has no access to any dispatch_blog_review_subagent result on "
            "its own. Use this once you've reviewed every post relevant to the focus."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "description": "The complete prior dispatch_blog_review_subagent result objects to synthesize.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "post_id": {"type": "string"},
                            "claim": {"type": "string"},
                            "evidence_excerpt": {"type": "string"},
                            "source": {
                                "type": "object",
                                "properties": {
                                    "blog_name": {"type": "string"},
                                    "author": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "focus": {"type": "string", "description": "What the destination summary should address."},
            },
            "required": ["findings", "focus"],
        },
    },
    {
        "name": "dispatch_itinerary_subagent",
        "description": (
            "Fork a shared destination-summary baseline into ONE divergent travel-style "
            "exploration ('budget' or 'luxury'). Call this twice in the SAME turn — once "
            "per style — passing the identical baseline_summary text to both, so each "
            "subagent departs from the same shared baseline but explores a different "
            "itinerary in isolation from the other."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "baseline_summary": {
                    "type": "string",
                    "description": "The summary text returned by dispatch_synthesis_subagent, unmodified.",
                },
                "style": {
                    "type": "string",
                    "enum": ["budget", "luxury"],
                    "description": "Which travel style this subagent should explore.",
                },
            },
            "required": ["baseline_summary", "style"],
        },
    },
]


def build_dispatcher(client, model: str):
    """Bind the coordinator's Anthropic client/model into a ToolDispatcher closure."""

    def dispatch_tool(tool_name: str, tool_input: dict) -> dict:
        if tool_name == "dispatch_blog_review_subagent":
            return _dispatch_blog_review_subagent(client, model, **tool_input)
        if tool_name == "dispatch_synthesis_subagent":
            return _dispatch_synthesis_subagent(client, model, **tool_input)
        if tool_name == "dispatch_itinerary_subagent":
            return _dispatch_itinerary_subagent(client, model, **tool_input)
        return tool_error("validation", False, f"Unknown tool '{tool_name}'.")

    return dispatch_tool
