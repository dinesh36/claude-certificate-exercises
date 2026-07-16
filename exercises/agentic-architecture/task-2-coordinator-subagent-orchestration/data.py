"""Mock research corpus for the exercise (Domain 1.2).

A small set of source documents about "remote work's impact on software
engineering teams", tagged by topic. dispatch_search_subagent in tools.py
reads from here — a real system would call a search API instead, but the
shallow/full split below is what makes the coordinator's iterative
refinement behavior (Task Statement 1.2's "re-delegate on gaps") observable
without needing a live search backend.
"""

# Valid values for the `topic_tag` tool parameter — the boundary of what the
# coordinator can choose to cover, and how it demonstrates (or fails to
# demonstrate) broad-enough decomposition of a query.
TOPIC_TAGS = [
    "productivity",
    "collaboration_tools",
    "employee_wellbeing",
    "security_risks",
    "onboarding_challenges",
]

# Each tag has 4 source snippets. A "shallow" search (deep_dive=False) only
# surfaces the first one, simulating a search subagent that found *a* result
# but not full coverage — the coordinator is expected to notice the
# accompanying gap_hint and decide whether the tag matters enough to the
# user's query to warrant a deep_dive follow-up before finalizing.
KNOWLEDGE_BASE: dict[str, list[str]] = {
    "productivity": [
        "A 2023 internal survey of 400 engineers found self-reported output rose 9% after switching to remote-first, driven mostly by fewer context-switching interruptions.",
        "Teams with more than 12 members saw productivity gains shrink to near zero, attributed to coordination overhead not offset by focus-time gains.",
        "Async standups (written, not synchronous) correlated with higher sprint completion rates across every team size studied.",
        "Engineers with dedicated home office space reported 20% higher focus-time scores than those working from shared/common spaces.",
    ],
    "collaboration_tools": [
        "Adoption of persistent virtual whiteboards reduced design-review turnaround from 4 days to 1.5 days on average.",
        "Teams relying solely on chat (no video) for architecture discussions reported more misunderstandings that surfaced later as rework.",
        "Recorded async video walkthroughs of PRs cut reviewer ramp-up time by roughly a third for cross-timezone teams.",
        "Tool sprawl (5+ overlapping chat/doc/video tools) was the single most cited source of onboarding friction in exit interviews.",
    ],
    "employee_wellbeing": [
        "Self-reported burnout scores rose in the first two quarters of remote transition, then fell below the office-baseline by month nine.",
        "Engineers who maintained a hard end-of-day calendar block reported significantly lower burnout scores than those without one.",
        "Isolation was the top-cited wellbeing concern among engineers with less than 2 years of tenure.",
        "Teams with a standing optional weekly informal video call reported higher belonging scores with no measurable productivity cost.",
    ],
    "security_risks": [
        "Unmanaged home routers accounted for the largest share of flagged endpoint vulnerabilities after the remote transition.",
        "Phishing click-through rates rose 15% in the first remote quarter before security-awareness refreshers brought them back down.",
        "Split-tunnel VPN configurations were linked to a higher rate of data-exfiltration alerts than full-tunnel configurations.",
        "Shadow-IT SaaS adoption (tools not vetted by security) roughly doubled once in-office peer oversight disappeared.",
    ],
    "onboarding_challenges": [
        "New hires took on average 3 weeks longer to reach first-PR-merged when onboarding fully remote versus in-office with a co-located buddy.",
        "Structured 30/60/90-day remote onboarding plans closed most of that gap versus ad hoc onboarding.",
        "New hires cited 'not knowing who to ask' as the top blocker in their first month, more than any technical issue.",
        "Pairing new hires with a dedicated onboarding buddy (not just their manager) was the single strongest predictor of faster ramp-up.",
    ],
}

# The first dispatch_search_subagent call for this tag raises an unhandled
# exception (simulating a subagent-side crash, e.g. a network timeout)
# instead of returning a result at all — used to exercise common/agent_loop.py's
# per-block exception handling rather than a tool-returned error dict.
FLAKY_TOPIC_TAG = "security_risks"
_flaky_attempts: dict[str, int] = {}
