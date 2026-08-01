"""Tool schemas and implementations (Domain 2).

_get_deployment_status and _list_deployments are deliberately similar —
both return deployment info — so their descriptions carry the
distinguishing boundary condition (exact ID in hand vs. not) to test
tool-selection accuracy rather than relying on the model to guess.

The only export is TOOLS: a list of {"schema": ..., "implementation": ...}
entries. common/agent_loop.py extracts the schemas for the Anthropic API call
and builds its own name -> implementation map to dispatch tool_use blocks
directly — nothing else in this module needs to be imported elsewhere.
"""

from common.errors import tool_error

from data import DEPLOYMENTS, SERVICES, _list_attempts, _next_deployment_id

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _get_deployment_status(deployment_id: str) -> dict:
    deployment = DEPLOYMENTS.get(deployment_id)
    if deployment is None:
        return tool_error(
            "validation",
            False,
            f"No deployment found with ID '{deployment_id}'. Verify the deployment ID.",
        )
    return {"deployment_id": deployment_id, **deployment}


def _list_deployments(service: str, environment: str = "") -> dict:
    if service not in SERVICES:
        return tool_error(
            "validation",
            False,
            f"No service found named '{service}'. Known services: {', '.join(sorted(SERVICES))}.",
        )

    # Simulate one transient failure per service to exercise retry handling.
    attempts = _list_attempts.get(service, 0)
    _list_attempts[service] = attempts + 1
    if attempts == 0:
        return tool_error(
            "transient",
            True,
            "Deployment inventory service timed out. Retry the request.",
        )

    matches = [
        {"deployment_id": did, **d}
        for did, d in DEPLOYMENTS.items()
        if d["service"] == service and (d["environment"] == environment if environment else True)
    ]
    return {"service": service, "matches": matches}


def _request_deploy(service: str, environment: str, version: str, risk_score: float) -> dict:
    if service not in SERVICES:
        return tool_error(
            "validation",
            False,
            f"No service found named '{service}'. Known services: {', '.join(sorted(SERVICES))}.",
        )
    if environment not in {"staging", "production"}:
        return tool_error(
            "validation",
            False,
            f"Unknown environment '{environment}'. Must be 'staging' or 'production'.",
        )
    deployment_id = _next_deployment_id()
    DEPLOYMENTS[deployment_id] = {
        "service": service,
        "environment": environment,
        "version": version,
        "status": "live",
        "risk_score": risk_score,
    }
    return {"deployment_id": deployment_id, "status": "deployed", **DEPLOYMENTS[deployment_id]}


def _escalate_to_oncall(
    service: str,
    environment: str,
    issue_summary: str,
    root_cause: str,
    recommended_action: str,
    deployment_id: str = "",
) -> dict:
    ticket_id = f"ESC-{abs(hash((service, issue_summary))) % 100000:05d}"
    return {
        "ticket_id": ticket_id,
        "service": service,
        "environment": environment,
        "deployment_id": deployment_id or None,
        "issue_summary": issue_summary,
        "root_cause": root_cause,
        "recommended_action": recommended_action,
        "status": "escalated_to_oncall_lead",
    }


# ---------------------------------------------------------------------------
# TOOLS — the only export: one {schema, implementation} entry per tool
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "schema": {
            "name": "get_deployment_status",
            "description": (
                "Fetch full status for a SINGLE deployment when you already have its exact "
                "deployment ID (format 'DEPLOY-XXXX'), e.g. because it was named in the request "
                "or returned by a prior tool call. Do NOT use this to browse or search — if you "
                "don't have an exact deployment ID yet, use list_deployments instead."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "deployment_id": {"type": "string", "description": "Exact deployment ID, e.g. 'DEPLOY-2005'."},
                },
                "required": ["deployment_id"],
            },
        },
        "implementation": _get_deployment_status,
    },
    {
        "schema": {
            "name": "list_deployments",
            "description": (
                "Look up a service's deployments when you do NOT have an exact deployment ID — "
                "e.g. 'what's currently running on checkout-api'. Requires the service name and "
                "optionally filters by environment. Do NOT use this if an exact deployment ID is "
                "already known; call get_deployment_status instead. This tool can fail with a "
                "transient error — retry once if so."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "description": "Exact service name, e.g. 'checkout-api'."},
                    "environment": {"type": "string", "description": "Optional filter: 'staging' or 'production'."},
                },
                "required": ["service"],
            },
        },
        "implementation": _list_deployments,
    },
    {
        "schema": {
            "name": "request_deploy",
            "description": (
                "Request a new deployment of a service version to an environment. Requires a "
                "risk_score (1-10) reflecting the change's blast radius. Production deploys above "
                "a policy risk threshold are automatically blocked and redirected to on-call "
                "escalation — do not attempt to work around this by resubmitting with a lower "
                "risk_score than the change actually warrants."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "description": "Exact service name to deploy."},
                    "environment": {"type": "string", "description": "'staging' or 'production'."},
                    "version": {"type": "string", "description": "Version being deployed, e.g. '4.2.0'."},
                    "risk_score": {"type": "number", "description": "Risk score from 1 (trivial) to 10 (severe)."},
                },
                "required": ["service", "environment", "version", "risk_score"],
            },
        },
        "implementation": _request_deploy,
    },
    {
        "schema": {
            "name": "escalate_to_oncall",
            "description": (
                "Hand off a deployment decision to the on-call lead. Use this when a deploy is "
                "blocked by the production risk-threshold policy, or when the issue cannot be "
                "resolved with the available tools. Produces a structured summary (root cause, "
                "recommended action) since the on-call lead has no access to this conversation "
                "transcript."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "environment": {"type": "string"},
                    "deployment_id": {"type": "string", "description": "Related deployment ID, if any."},
                    "issue_summary": {"type": "string", "description": "One-paragraph summary of the request."},
                    "root_cause": {"type": "string", "description": "Why the request needs escalation."},
                    "recommended_action": {"type": "string", "description": "What the on-call lead should do next."},
                },
                "required": ["service", "environment", "issue_summary", "root_cause", "recommended_action"],
            },
        },
        "implementation": _escalate_to_oncall,
    },
]
