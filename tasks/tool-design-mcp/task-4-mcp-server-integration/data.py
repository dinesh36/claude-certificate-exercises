"""Mock engineering docs catalog for the integration MCP server (Domain 2.4).

Each doc has a section and a set of tags, so search_docs can match on
structure (section, tags) as well as title -- not just raw text -- and the
docs://catalog resource can group them by section for the agent to browse.
"""

DOCS = {
    "RUNBOOK-DB-FAILOVER": {
        "title": "Database Failover Runbook",
        "section": "Runbooks",
        "tags": ["database", "failover", "on-call", "incident"],
        "body": (
            "1. Confirm the primary is actually down (check the replica lag dashboard).\n"
            "2. Promote the healthiest replica using `pg_promote`.\n"
            "3. Update the connection string in the app config and redeploy.\n"
            "4. Page the database team lead once failover is confirmed."
        ),
    },
    "RUNBOOK-ONCALL-ESCALATION": {
        "title": "On-Call Escalation Policy",
        "section": "Runbooks",
        "tags": ["on-call", "escalation", "incident"],
        "body": (
            "Page the primary on-call first. If no ack within 10 minutes, page the "
            "secondary. If still no ack after 20 minutes total, escalate to the "
            "engineering manager on the incident channel."
        ),
    },
    "DOC-API-VERSIONING": {
        "title": "API Versioning Standards",
        "section": "Standards",
        "tags": ["api", "versioning", "backwards-compatibility"],
        "body": (
            "All public APIs are versioned under /v{N}/. Breaking changes require a new "
            "major version. Additive changes (new optional fields) may ship under the "
            "existing version."
        ),
    },
    "DOC-CODE-REVIEW": {
        "title": "Code Review Guidelines",
        "section": "Standards",
        "tags": ["code-review", "process"],
        "body": (
            "Every PR needs one approval before merge. Reviewers should focus on "
            "correctness and design first, style nits second. Author responds to every "
            "comment thread before merging."
        ),
    },
    "DOC-ONBOARDING": {
        "title": "New Engineer Onboarding Guide",
        "section": "Onboarding",
        "tags": ["onboarding", "setup"],
        "body": (
            "Day 1: get repo access, set up local dev environment, read the architecture "
            "overview. Week 1: ship a small fix with a reviewer. Week 2: join the on-call "
            "shadow rotation."
        ),
    },
}
