"""Internal Anthropic-API subagent pipeline for the insurance claims desk (Domain 2.3).

Each stage below is an ISOLATED Anthropic Messages API call (its own
common.agent_loop.run_tool_loop invocation) with its own, deliberately
narrow tools list scoped to that stage's role — never the full
internal_tools.py set. Restricting each subagent's tools to only what its
role needs is what prevents the cross-specialization misuse (e.g. a
synthesis agent attempting a coverage lookup) this task statement calls out.

The intake stage additionally forces its first tool call via
`initial_tool_choice` (extract_claim_metadata must run before
flag_missing_documents is even considered), then lets follow-up turns
choose freely; classify_claim forces `{"type": "any"}` so it can never
return prose instead of a structured tool result.
"""

from common.agent_loop import run_tool_loop
from common.client import DEFAULT_MODEL, get_client
from internal_tools import ASSESSOR_TOOLS, CLASSIFY_TOOLS, INTAKE_TOOLS, SYNTHESIS_TOOLS

_client = get_client()
_model = DEFAULT_MODEL


def run_intake(claim_id: str) -> str:
    result = run_tool_loop(
        client=_client,
        model=_model,
        system=(
            "You are the INTAKE specialist on an insurance claims desk. You only have tools "
            "for extracting claim metadata and checking for missing documents — you cannot look "
            "up policy coverage or draft customer letters; those are different specialists' jobs."
        ),
        tools=INTAKE_TOOLS,
        user_message=f"Process intake for claim {claim_id}.",
        initial_tool_choice={"type": "tool", "name": "extract_claim_metadata"},
    )
    return result.final_text


def run_assessment(claim_id: str, intake_summary: str) -> str:
    result = run_tool_loop(
        client=_client,
        model=_model,
        system=(
            "You are the COVERAGE ASSESSOR on an insurance claims desk. You only have policy "
            "lookup and coverage-check tools — you cannot extract intake metadata or draft "
            "customer letters; those are different specialists' jobs. Determine whether this "
            "claim is covered and up to what limit."
        ),
        tools=ASSESSOR_TOOLS,
        user_message=f"Assess coverage for claim {claim_id}. Intake summary: {intake_summary}",
    )
    return result.final_text


def run_synthesis(claim_id: str, intake_summary: str, assessment_summary: str) -> str:
    result = run_tool_loop(
        client=_client,
        model=_model,
        system=(
            "You are the CUSTOMER-LETTER specialist on an insurance claims desk. You cannot "
            "look up policy details or run coverage checks yourself — route anything you're "
            "unsure of back to the coordinator instead of guessing. The one exception is "
            "verify_claim_fact, a narrow tool for double-checking a single already-known fact "
            "before it goes in a letter. Draft the customer letter from the intake and "
            "assessment summaries you were given."
        ),
        tools=SYNTHESIS_TOOLS,
        user_message=(
            f"Draft the customer letter for claim {claim_id}.\n"
            f"Intake summary: {intake_summary}\nAssessment summary: {assessment_summary}"
        ),
    )
    return result.final_text


def run_classification(claim_id: str) -> str:
    result = run_tool_loop(
        client=_client,
        model=_model,
        system="You classify insurance claim urgency. Always call the classification tool — never answer in prose.",
        tools=CLASSIFY_TOOLS,
        user_message=f"Classify the urgency of claim {claim_id}.",
        initial_tool_choice={"type": "any"},
    )
    return result.final_text
