"""Mock legacy-codebase data for the migration-analysis coordinator (Domain 1.7).

MODULES backs the baseline investigation (list_modules/analyze_module).
CHANGES_SINCE_BASELINE backs the resume path — describes what actually
changed in one module after the baseline was run, so a resumed session can
be told about it directly instead of re-exploring every module from
scratch. MIGRATION_ESTIMATES backs the fork path — estimate_migration_effort
returns a genuinely different effort/risk profile per (strategy, module)
pair, so two forked sessions asking about different strategies get
different answers from the same shared baseline.
"""

MODULES = {
    "billing": {"loc": 4200, "coupling_score": 8, "test_coverage_pct": 22, "last_changed": "2024-01-10"},
    "auth": {"loc": 1800, "coupling_score": 3, "test_coverage_pct": 71, "last_changed": "2023-11-02"},
    "reporting": {"loc": 6100, "coupling_score": 9, "test_coverage_pct": 15, "last_changed": "2024-02-20"},
}

# What changed in a module after the baseline investigation ran — only
# populated for modules that actually changed, so check_module_diff can
# report "no recorded change" for anything else.
CHANGES_SINCE_BASELINE = {
    "billing": (
        "Since the baseline analysis, billing had a new `invoicing` submodule extracted "
        "out of it, cutting its direct dependents from 8 down to 3 — the baseline's "
        "coupling_score of 8 no longer reflects its current state."
    ),
}

MIGRATION_ESTIMATES = {
    ("strangler-fig", "billing"): {
        "estimated_weeks": 10,
        "risk": "low",
        "notes": (
            "Route new invoicing traffic through the new submodule first; legacy billing "
            "keeps running untouched until fully drained."
        ),
    },
    ("big-bang", "billing"): {
        "estimated_weeks": 4,
        "risk": "high",
        "notes": (
            "Rewrite billing in one release; high risk given its 22% test coverage leaves "
            "regressions hard to catch before launch."
        ),
    },
    ("strangler-fig", "reporting"): {
        "estimated_weeks": 14,
        "risk": "medium",
        "notes": (
            "Reporting's high coupling (9 dependents) means an incremental cutover needs a "
            "compatibility shim layer during the transition."
        ),
    },
    ("big-bang", "reporting"): {
        "estimated_weeks": 6,
        "risk": "high",
        "notes": (
            "A single-release rewrite of reporting's 6.1k LOC with only 15% test coverage "
            "risks silent breakage across every dependent module."
        ),
    },
}
