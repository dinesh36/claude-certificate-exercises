"""
Preparation Exercise 4: Multi-Agent Research Pipeline
Domains reinforced: 1 (Agentic Architecture & Orchestration), 2 (Tool Design & MCP Integration),
5 (Context Management & Reliability)

A research coordinator studying renewable-energy adoption rates across four
regions, dispatching two independent subagent sources per region (an
industry analyst report and a government statistics bulletin). Demonstrates
parallel subagent dispatch with a measured latency improvement over
sequential calls, claim/evidence/source/date structured findings, a
persistently failing subagent (proceed with partial results instead of
retrying forever), and conflicting-source synthesis that preserves both
values with attribution instead of picking one.

See tools.py for the two dispatch tools/subagents and data.py for the mock
report/bulletin sources.
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from common.agent_loop import run_tool_loop
from common.client import DEFAULT_MODEL, get_client

from data import SIMULATED_SUBAGENT_LATENCY_SECONDS
from tools import TOOLS

client = get_client()

SYSTEM_PROMPT = (
    "You are a research coordinator studying renewable-energy adoption rates across regions. "
    "You have two subagent tools: dispatch_industry_report_subagent (an industry analyst "
    "report) and dispatch_government_data_subagent (an independent government statistics "
    "source). For every region you need, call both subagents so each claim has two "
    "independent sources where possible — emit all the calls you need together in the same "
    "turn, not one at a time. Every subagent call returns a finding with a claim, "
    "evidence_excerpt, a source (name/url), and a publication_date — preserve all of these "
    "when you report back, never just a bare number. If a subagent call fails with a "
    "transient error, you may retry it once; if it fails again, proceed with the data you do "
    "have for that region and explicitly note the coverage gap in your final report rather "
    "than retrying indefinitely or fabricating a number for the missing source. When two "
    "sources report different figures for the same region, report the discrepancy "
    "explicitly — both numbers, both sources — do not average them, and do not silently pick "
    "one. Structure your final report in two sections: 'Well-established findings' (sources "
    "agree) and 'Contested findings' (sources disagree), plus a 'Coverage gaps' note for any "
    "region missing a source."
)


def _simulate_subagent_call() -> None:
    """Stands in for one subagent dispatch's real latency (the same
    SIMULATED_SUBAGENT_LATENCY_SECONDS sleep tools.py's dispatch
    implementations use) — used only to measure concurrent vs. sequential
    timing, decoupled from the live coordinator run below."""
    time.sleep(SIMULATED_SUBAGENT_LATENCY_SECONDS)


def measure_dispatch_latency(call_count: int) -> tuple[float, float]:
    """Return (concurrent_seconds, sequential_seconds) for dispatching
    `call_count` subagent calls both ways — a real, measured comparison,
    not an estimate."""
    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=call_count) as pool:
        futures = [pool.submit(_simulate_subagent_call) for _ in range(call_count)]
        for future in as_completed(futures):
            future.result()
    concurrent_seconds = time.monotonic() - start

    start = time.monotonic()
    for _ in range(call_count):
        _simulate_subagent_call()
    sequential_seconds = time.monotonic() - start

    return concurrent_seconds, sequential_seconds


if __name__ == "__main__":
    scenario = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "What's the current renewable-energy adoption rate in California, Texas, Germany, "
            "and Japan? Use both the industry report and government data sources for each."
        )
    )

    call_count = 8  # 4 regions x 2 sources, matching the default scenario's dispatch count
    concurrent_seconds, sequential_seconds = measure_dispatch_latency(call_count)
    print(
        f"=== Parallel vs sequential dispatch latency ({call_count} simulated subagent calls) ===\n"
        f"Concurrent: {concurrent_seconds:.2f}s\n"
        f"Sequential: {sequential_seconds:.2f}s\n"
        f"Speedup: {sequential_seconds / concurrent_seconds:.1f}x\n"
    )

    print(f"User: {scenario}\n")
    result = run_tool_loop(
        client=client,
        model=DEFAULT_MODEL,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        user_message=scenario,
        max_tokens=4096,
    )
    print(f"\nAgent: {result.final_text}")
