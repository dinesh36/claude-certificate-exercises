"""Mock insurance-claims-desk data for the tool-distribution MCP server (Domain 2.3).

CLAIMS backs every stage of the pipeline — metadata is pre-structured here
(not parsed from raw_narrative) to keep the demo deterministic, the same way
earlier tasks store mock "extracted" facts directly rather than parsing free
text. POLICIES backs the assessor stage's lookup_policy/check_coverage.
REQUIRED_DOCUMENTS backs the intake stage's flag_missing_documents.
"""

CLAIMS = {
    "CLAIM-1001": {
        "raw_narrative": (
            "Claimant Jane Doe reports a rear-end collision on Highway 12 on "
            "2026-03-01, requesting $4,200 for vehicle repair."
        ),
        "claimant_name": "Jane Doe",
        "incident_type": "auto_collision",
        "amount_claimed": 4200,
        "policy_number": "POL-55",
        "documents_submitted": ["police_report"],
    },
    "CLAIM-1002": {
        "raw_narrative": (
            "Claimant Mike Chen reports water damage to his basement from a burst "
            "pipe on 2026-02-15, requesting $18,500 for repairs."
        ),
        "claimant_name": "Mike Chen",
        "incident_type": "water_damage",
        "amount_claimed": 18500,
        "policy_number": "POL-77",
        "documents_submitted": ["photos", "plumber_invoice", "police_report"],
    },
}

POLICIES = {
    "POL-55": {
        "holder": "Jane Doe",
        "status": "active",
        "deductible": 500,
        "coverage_limits": {"auto_collision": 5000},
    },
    "POL-77": {
        "holder": "Mike Chen",
        "status": "active",
        "deductible": 1000,
        "coverage_limits": {"water_damage": 10000},
    },
}

REQUIRED_DOCUMENTS = {
    "auto_collision": ["police_report", "photos"],
    "water_damage": ["photos", "plumber_invoice"],
}
