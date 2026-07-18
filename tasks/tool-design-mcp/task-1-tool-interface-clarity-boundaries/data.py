"""Mock backlog/bug-tracker data for the dev-workflow MCP server (Domain 2.1).

USER_STORIES and BUG_TICKETS are deliberately two separate stores with two
separate ID prefixes ("STORY-" vs "BUG-") — this is what lets
fetch_user_story/fetch_bug_ticket give a precise, corrective error when
called with the other kind of ID, instead of silently returning nothing or
the wrong shape.
"""

USER_STORIES = {
    "STORY-101": {
        "title": "Add CSV export to the reporting dashboard",
        "description": (
            "As an analyst, I want to export the current dashboard view to CSV so I can "
            "share results outside the app."
        ),
        "acceptance_criteria": [
            "Export button appears on every dashboard view",
            "CSV includes all visible columns and current filters applied",
            "Export completes in under 5 seconds for up to 10,000 rows",
        ],
        "dependencies": ["Dashboard filtering must be finalized (STORY-098)"],
    },
    "STORY-102": {
        "title": "Allow users to schedule recurring report emails",
        "description": (
            "As a manager, I want reports emailed to me on a recurring schedule so I don't "
            "have to check the dashboard manually."
        ),
        "acceptance_criteria": [
            "User can pick daily/weekly/monthly cadence",
            "Emails include a PDF snapshot of the report",
        ],
        "dependencies": [],
    },
}

BUG_TICKETS = {
    "BUG-501": {
        "title": "Dashboard export button unresponsive on Safari",
        "severity": "medium",
        "repro_steps": [
            "Open dashboard in Safari 17",
            "Apply any filter",
            "Click Export to CSV",
        ],
        "expected": "CSV downloads",
        "actual": "Button shows a spinner indefinitely, no download starts",
    },
}
