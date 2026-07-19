"""Anthropic tool_use schemas/implementations for the internal subagent pipeline
(Domain 2.3) — NOT MCP tools. server.py's two MCP-exposed tools each dispatch to
one or more of these subagents via common/agent_loop.py's run_tool_loop; Claude
Code never sees these schemas directly.

Grouped into four deliberately narrow, role-scoped lists — INTAKE_TOOLS,
ASSESSOR_TOOLS, SYNTHESIS_TOOLS, CLASSIFY_TOOLS — each handed to a different
subagent in pipeline.py. No subagent ever receives the full set: the intake
subagent can't look up policy coverage, the assessor can't draft letters, and
the synthesis subagent's only lookup is the one narrow verify_claim_fact tool
— restricting each subagent's tools to its own role is the mechanism this task
statement is about, not an incidental detail.
"""

from common.errors import tool_error

from data import CLAIMS, POLICIES, REQUIRED_DOCUMENTS

# Facts verify_claim_fact is allowed to answer — a narrow cross-role tool, not
# full read access to the claim record (see the Synthesis subagent below).
_VERIFIABLE_FACTS = {"claimant_name", "incident_type", "amount_claimed", "policy_number"}


def _get_claim(claim_id: str) -> dict:
    claim = CLAIMS.get(claim_id)
    if claim is None:
        return tool_error("validation", False, f"No claim found with ID '{claim_id}'. Known claims: {', '.join(CLAIMS)}.")
    return claim


# --- Intake stage ---------------------------------------------------------


def _extract_claim_metadata(claim_id: str) -> dict:
    claim = _get_claim(claim_id)
    if "errorCategory" in claim:
        return claim
    return {
        "claim_id": claim_id,
        "claimant_name": claim["claimant_name"],
        "incident_type": claim["incident_type"],
        "amount_claimed": claim["amount_claimed"],
        "policy_number": claim["policy_number"],
    }


def _flag_missing_documents(claim_id: str) -> dict:
    claim = _get_claim(claim_id)
    if "errorCategory" in claim:
        return claim
    required = REQUIRED_DOCUMENTS.get(claim["incident_type"], [])
    missing = [doc for doc in required if doc not in claim["documents_submitted"]]
    return {"claim_id": claim_id, "required": required, "submitted": claim["documents_submitted"], "missing": missing}


# --- Assessor stage --------------------------------------------------------


def _lookup_policy(policy_number: str) -> dict:
    policy = POLICIES.get(policy_number)
    if policy is None:
        return tool_error("validation", False, f"No policy found with number '{policy_number}'.")
    return {"policy_number": policy_number, **policy}


def _check_coverage(policy_number: str, incident_type: str) -> dict:
    policy = POLICIES.get(policy_number)
    if policy is None:
        return tool_error("validation", False, f"No policy found with number '{policy_number}'.")
    limit = policy["coverage_limits"].get(incident_type)
    return {
        "policy_number": policy_number,
        "incident_type": incident_type,
        "covered": limit is not None,
        "coverage_limit": limit,
        "deductible": policy["deductible"],
    }


# --- Synthesis stage ---------------------------------------------------------


def _verify_claim_fact(claim_id: str, fact: str) -> dict:
    if fact not in _VERIFIABLE_FACTS:
        return tool_error(
            "validation",
            False,
            f"'{fact}' isn't a fact this tool can verify. Known facts: {', '.join(_VERIFIABLE_FACTS)}. "
            "For anything else, route the question back through the coordinator instead of guessing.",
        )
    claim = _get_claim(claim_id)
    if "errorCategory" in claim:
        return claim
    return {"claim_id": claim_id, "fact": fact, "value": claim[fact]}


def _draft_customer_letter(claim_id: str, decision: str, reason: str) -> dict:
    claim = _get_claim(claim_id)
    if "errorCategory" in claim:
        return claim
    letter = (
        f"Dear {claim['claimant_name']},\n\n"
        f"Regarding your claim {claim_id}: your claim has been {decision}. {reason}\n\n"
        "Sincerely,\nClaims Desk"
    )
    return {"claim_id": claim_id, "decision": decision, "letter": letter}


# --- Classification stage ---------------------------------------------------


def _classify_claim_urgency(claim_id: str) -> dict:
    claim = _get_claim(claim_id)
    if "errorCategory" in claim:
        return claim
    amount = claim["amount_claimed"]
    urgency = "high" if amount > 10000 else "medium" if amount > 3000 else "low"
    return {"claim_id": claim_id, "amount_claimed": amount, "urgency": urgency}


INTAKE_TOOLS = [
    {
        "schema": {
            "name": "extract_claim_metadata",
            "description": (
                "Extract structured metadata (claimant name, incident type, amount claimed, "
                "policy number) from a claim record. Call this FIRST for any new claim, before "
                "flag_missing_documents — you need the incident type before you can know which "
                "documents are required."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"claim_id": {"type": "string", "description": "e.g. 'CLAIM-1001'."}},
                "required": ["claim_id"],
            },
        },
        "implementation": _extract_claim_metadata,
    },
    {
        "schema": {
            "name": "flag_missing_documents",
            "description": (
                "Check which required documents (based on incident type) are missing from a "
                "claim. Call this AFTER extract_claim_metadata, once you know the incident type — "
                "this is an enrichment step, not the first thing to reach for."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"claim_id": {"type": "string", "description": "e.g. 'CLAIM-1001'."}},
                "required": ["claim_id"],
            },
        },
        "implementation": _flag_missing_documents,
    },
]

ASSESSOR_TOOLS = [
    {
        "schema": {
            "name": "lookup_policy",
            "description": (
                "Look up a policy's holder, status, deductible, and coverage limits by policy "
                "number. Use this to confirm the policy is active before checking coverage."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"policy_number": {"type": "string", "description": "e.g. 'POL-55'."}},
                "required": ["policy_number"],
            },
        },
        "implementation": _lookup_policy,
    },
    {
        "schema": {
            "name": "check_coverage",
            "description": (
                "Check whether a specific incident type is covered under a policy, and up to "
                "what limit. Call this once you know the policy number and incident type."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "policy_number": {"type": "string", "description": "e.g. 'POL-55'."},
                    "incident_type": {"type": "string", "description": "e.g. 'auto_collision'."},
                },
                "required": ["policy_number", "incident_type"],
            },
        },
        "implementation": _check_coverage,
    },
]

SYNTHESIS_TOOLS = [
    {
        "schema": {
            "name": "verify_claim_fact",
            "description": (
                "Double-check ONE specific already-known fact about a claim (claimant_name, "
                "incident_type, amount_claimed, or policy_number) before it goes into a customer "
                "letter. This is a narrow spot-check, not a general lookup tool — it cannot look "
                "up policy coverage or anything not already summarized for you; route anything "
                "else back through the coordinator instead of guessing."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string", "description": "e.g. 'CLAIM-1001'."},
                    "fact": {
                        "type": "string",
                        "enum": sorted(_VERIFIABLE_FACTS),
                        "description": "Which single fact to verify.",
                    },
                },
                "required": ["claim_id", "fact"],
            },
        },
        "implementation": _verify_claim_fact,
    },
    {
        "schema": {
            "name": "draft_customer_letter",
            "description": (
                "Draft the customer-facing decision letter for a claim, given a decision "
                "('approved', 'denied', or 'partial') and a one-sentence reason."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string", "description": "e.g. 'CLAIM-1001'."},
                    "decision": {"type": "string", "enum": ["approved", "denied", "partial"]},
                    "reason": {"type": "string", "description": "One sentence explaining the decision."},
                },
                "required": ["claim_id", "decision", "reason"],
            },
        },
        "implementation": _draft_customer_letter,
    },
]

CLASSIFY_TOOLS = [
    {
        "schema": {
            "name": "classify_claim_urgency",
            "description": "Classify a claim's urgency (low/medium/high) based on the amount claimed.",
            "input_schema": {
                "type": "object",
                "properties": {"claim_id": {"type": "string", "description": "e.g. 'CLAIM-1001'."}},
                "required": ["claim_id"],
            },
        },
        "implementation": _classify_claim_urgency,
    },
]
