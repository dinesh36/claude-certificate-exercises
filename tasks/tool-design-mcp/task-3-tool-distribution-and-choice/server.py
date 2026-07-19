"""
Task 3: Tool Distribution & Choice
Domain: Tool Design & MCP Integration — Task Statement 2.3

An insurance-claims-desk MCP server whose two MCP-exposed tools each
orchestrate their own internal Anthropic API subagent pipeline
(pipeline.py) — the hybrid this task statement needs, since tool_choice
has no MCP-protocol equivalent at all: it's a Messages API request
parameter Claude Code's own harness manages when *it* calls the model, not
something an MCP server's tool definitions can express. Putting a real
Anthropic API call inside an MCP tool's implementation is what lets this
task demonstrate tool_choice genuinely, rather than only the tool-scoping
half of the task statement.

process_claim runs three role-scoped subagents in sequence (intake,
assessment, synthesis) — each restricted to only the tools its role needs,
demonstrating that a synthesis agent doesn't get policy-lookup tools and an
intake agent doesn't get drafting tools. The intake subagent's first tool
call is forced (tool_choice: {"type": "tool", "name": "extract_claim_metadata"})
before its follow-up turns are free to choose. classify_claim runs a single
subagent with tool_choice: {"type": "any"}, guaranteeing a structured
classification instead of a conversational reply.

See data.py for the mock claim/policy data, internal_tools.py for the four
role-scoped Anthropic tool_use lists, and pipeline.py for the subagent
orchestration itself.
"""

from mcp.server.fastmcp import FastMCP

from common.errors import StructuredToolError
from common.mcp_logging import logged_tool
from data import CLAIMS
from pipeline import run_assessment, run_classification, run_intake, run_synthesis

SERVER_NAME = "insurance-claims-desk"

mcp = FastMCP(SERVER_NAME)


def _require_known_claim(claim_id: str) -> None:
    if claim_id not in CLAIMS:
        raise StructuredToolError("validation", False, f"No claim found with ID '{claim_id}'. Known claims: {', '.join(CLAIMS)}.")


@mcp.tool()
@logged_tool(SERVER_NAME)
def process_claim(claim_id: str) -> dict:
    """Process an insurance claim end to end through three role-scoped subagents.

    Runs intake (metadata extraction, forced first, then missing-document
    checks), coverage assessment (policy lookup and coverage check), and
    customer-letter synthesis, in that order — each stage is a separate
    Anthropic API call with only the tools relevant to its own role.

    Args:
        claim_id: Exact claim ID, e.g. "CLAIM-1001".

    Returns:
        A dict with `claim_id`, `intake_summary`, `assessment_summary`, and
        `customer_letter` — the output of each of the three subagent stages.

    Raises:
        StructuredToolError: errorCategory "validation", isRetryable False,
            if claim_id is unknown.
    """
    _require_known_claim(claim_id)

    intake_summary = run_intake(claim_id)
    assessment_summary = run_assessment(claim_id, intake_summary)
    customer_letter = run_synthesis(claim_id, intake_summary, assessment_summary)

    return {
        "claim_id": claim_id,
        "intake_summary": intake_summary,
        "assessment_summary": assessment_summary,
        "customer_letter": customer_letter,
    }


@mcp.tool()
@logged_tool(SERVER_NAME)
def classify_claim(claim_id: str) -> dict:
    """Classify a claim's urgency (low/medium/high) via a forced tool call.

    Unlike process_claim, this runs a single subagent with
    tool_choice: {"type": "any"} — guaranteeing the model calls
    classify_claim_urgency rather than returning a conversational answer.

    Args:
        claim_id: Exact claim ID, e.g. "CLAIM-1001".

    Returns:
        A dict with `claim_id` and `classification` (the subagent's reply,
        grounded in a real classify_claim_urgency tool call).

    Raises:
        StructuredToolError: errorCategory "validation", isRetryable False,
            if claim_id is unknown.
    """
    _require_known_claim(claim_id)
    return {"claim_id": claim_id, "classification": run_classification(claim_id)}


if __name__ == "__main__":
    mcp.run()
