"""Tool schemas and implementations for the coordinator (Domain 1.2/1.3).

Both dispatch tools call an isolated subagent (common.subagent.run_subagent)
rather than answering directly — the subagent only ever sees what this
module explicitly forwards in `user_message`, never the coordinator's own
conversation history. Each dispatch also sleeps
SIMULATED_SUBAGENT_LATENCY_SECONDS before returning, standing in for a real
network/API call's latency — main.py's standalone timing demonstration
reuses this same constant, so the measured concurrent-vs-sequential speedup
is a real number, not a fabricated one.

The only export is TOOLS: a list of {"schema": ..., "implementation": ...}
entries. Subagent calls need their own Anthropic client/model, so this
module creates its own (_client/_model below) rather than taking them as
parameters — that binding work stays entirely in this file.
"""

import time

from common.client import DEFAULT_MODEL, get_client
from common.errors import tool_error
from common.subagent import run_subagent

from data import GOVERNMENT_DATA, INDUSTRY_REPORTS, REGIONS, SIMULATED_SUBAGENT_LATENCY_SECONDS

_client = get_client()
_model = DEFAULT_MODEL

REPORT_SUBAGENT_SYSTEM = (
    "You are a research subagent reading one industry analyst report excerpt. You have no "
    "knowledge of the original research question, the coordinator's plan, or any other "
    "subagent's output — you only know the excerpt given below. Restate its key claim in "
    "one sentence."
)

DATA_SUBAGENT_SYSTEM = (
    "You are a research subagent reading one government statistics bulletin excerpt. You "
    "have no knowledge of the original research question, the coordinator's plan, or any "
    "other subagent's output — you only know the excerpt given below. Restate its key claim "
    "in one sentence."
)


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _dispatch_industry_report_subagent(region: str) -> dict:
    if region not in REGIONS:
        return tool_error("validation", False, f"Unknown region '{region}'. Valid regions: {', '.join(REGIONS)}.")

    time.sleep(SIMULATED_SUBAGENT_LATENCY_SECONDS)
    report = INDUSTRY_REPORTS[region]
    summary = run_subagent(_client, _model, REPORT_SUBAGENT_SYSTEM, f"Report excerpt: {report['evidence_excerpt']}")
    return {
        "region": region,
        "claim": report["claim"],
        "evidence_excerpt": report["evidence_excerpt"],
        "subagent_summary": summary,
        "source": {"name": report["source_name"], "url": report["source_url"]},
        "publication_date": report["publication_date"],
    }


def _dispatch_government_data_subagent(region: str) -> dict:
    if region not in REGIONS:
        return tool_error("validation", False, f"Unknown region '{region}'. Valid regions: {', '.join(REGIONS)}.")

    time.sleep(SIMULATED_SUBAGENT_LATENCY_SECONDS)
    record = GOVERNMENT_DATA[region]
    if record is None:
        return tool_error(
            "transient",
            True,
            (
                f"Timeout querying the government statistics feed. Failure type: "
                f"connection_timeout. Attempted query: region='{region}', "
                "dataset='renewable_adoption_rate'. This feed has been unavailable across "
                "repeated attempts for this region — if a retry also fails, proceed with only "
                "the industry-report finding for this region and note the coverage gap rather "
                "than retrying indefinitely."
            ),
        )
    summary = run_subagent(_client, _model, DATA_SUBAGENT_SYSTEM, f"Bulletin excerpt: {record['evidence_excerpt']}")
    return {
        "region": region,
        "claim": record["claim"],
        "evidence_excerpt": record["evidence_excerpt"],
        "subagent_summary": summary,
        "source": {"name": record["source_name"], "url": record["source_url"]},
        "publication_date": record["publication_date"],
    }


# ---------------------------------------------------------------------------
# TOOLS — the only export: one {schema, implementation} entry per tool
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "schema": {
            "name": "dispatch_industry_report_subagent",
            "description": (
                "Get one region's renewable-adoption finding from the industry analyst report "
                "source. Emit one call per region you need reviewed; to review several regions, "
                "emit all the calls you need together in this same turn rather than one at a "
                "time across separate turns."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"region": {"type": "string", "description": f"One of: {', '.join(REGIONS)}."}},
                "required": ["region"],
            },
        },
        "implementation": _dispatch_industry_report_subagent,
    },
    {
        "schema": {
            "name": "dispatch_government_data_subagent",
            "description": (
                "Get one region's renewable-adoption finding from the official government "
                "statistics source — an independent second source from the industry report. "
                "Emit one call per region you need, together in the same turn as any other "
                "calls. This tool can fail with a transient error for a region whose feed is "
                "down; if it fails again on retry, proceed without that region's government "
                "data rather than retrying indefinitely."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"region": {"type": "string", "description": f"One of: {', '.join(REGIONS)}."}},
                "required": ["region"],
            },
        },
        "implementation": _dispatch_government_data_subagent,
    },
]
