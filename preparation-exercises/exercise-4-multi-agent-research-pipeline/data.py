"""Mock renewable-energy research sources for the coordinator's subagents.

Two independent sources per region: an industry analyst report and an
official government statistics bulletin. Texas's two sources deliberately
report different adoption figures for the same claim (Step 5's conflicting-
source case); Germany's government feed is deliberately always down
(Step 4's error-propagation case, not a one-time flake).
"""

REGIONS = ["california", "texas", "germany", "japan"]

INDUSTRY_REPORTS = {
    "california": {
        "claim": "Solar accounts for 34% of California's utility-scale generation as of Q2 2025.",
        "evidence_excerpt": (
            "\"Utility-scale solar capacity additions pushed California's solar share of "
            "generation to 34% in Q2 2025, up from 29% a year earlier.\""
        ),
        "source_name": "GreenGrid Analytics — 2025 Utility Solar Report",
        "source_url": "https://greengrid-analytics.example/reports/2025-utility-solar",
        "publication_date": "2025-07-14",
    },
    "texas": {
        "claim": "Wind adoption in Texas reached 28% of grid generation in the latest reporting period.",
        "evidence_excerpt": (
            "\"ERCOT-connected wind capacity now supplies an estimated 28% of Texas grid "
            "generation, the highest of any U.S. state.\""
        ),
        "source_name": "GreenGrid Analytics — 2025 Wind Market Report",
        "source_url": "https://greengrid-analytics.example/reports/2025-wind-market",
        "publication_date": "2025-06-02",
    },
    "germany": {
        "claim": "Germany's combined solar and wind share of electricity generation exceeded 45% in 2025.",
        "evidence_excerpt": (
            "\"Combined wind and solar generation surpassed 45% of Germany's electricity mix "
            "for the first half of 2025.\""
        ),
        "source_name": "GreenGrid Analytics — 2025 European Renewables Report",
        "source_url": "https://greengrid-analytics.example/reports/2025-european-renewables",
        "publication_date": "2025-08-01",
    },
    "japan": {
        "claim": "Japan's solar adoption grew to 11% of total generation following continued rooftop incentives.",
        "evidence_excerpt": (
            "\"Rooftop solar incentive programs helped push Japan's solar share to an "
            "estimated 11% of total generation in 2025.\""
        ),
        "source_name": "GreenGrid Analytics — 2025 Asia-Pacific Solar Report",
        "source_url": "https://greengrid-analytics.example/reports/2025-apac-solar",
        "publication_date": "2025-05-20",
    },
}

# `None` for a region means that source's feed is simulated as persistently
# unavailable — not a one-time flake, so retrying alone can't fix it.
GOVERNMENT_DATA = {
    "california": {
        "claim": "California state energy data shows solar at 33% of utility-scale generation for Q2 2025.",
        "evidence_excerpt": "\"Q2 2025 grid mix: solar 33%, wind 8%, natural gas 41%, other 18%.\"",
        "source_name": "California Energy Commission — Quarterly Grid Mix Bulletin",
        "source_url": "https://energy.ca.gov.example/bulletins/2025-q2-grid-mix",
        "publication_date": "2025-07-20",
    },
    "texas": {
        "claim": "Texas state filing reports wind at 24% of grid generation for the latest period.",
        "evidence_excerpt": (
            "\"Wind generation accounted for 24% of ERCOT grid supply in the most recent "
            "reporting period.\""
        ),
        "source_name": "Texas Public Utility Commission — Grid Generation Filing",
        "source_url": "https://puc.texas.gov.example/filings/2025-grid-generation",
        "publication_date": "2025-06-10",
    },
    "germany": None,
    "japan": {
        "claim": "Japan METI data confirms solar at 11% of total generation for 2025.",
        "evidence_excerpt": (
            "\"METI's 2025 energy mix update lists solar at 11% of total electricity "
            "generation, consistent with prior-year growth trends.\""
        ),
        "source_name": "Japan Ministry of Economy, Trade and Industry — Energy Mix Update",
        "source_url": "https://meti.go.jp.example/energy-mix/2025-update",
        "publication_date": "2025-05-25",
    },
}

# Stands in for one subagent call's real network/API latency — the same
# constant is used by tools.py's dispatch implementations and main.py's
# standalone concurrent-vs-sequential timing demonstration, so the measured
# speedup reflects a real, shared number rather than two made-up ones.
SIMULATED_SUBAGENT_LATENCY_SECONDS = 0.5
