"""Tool schemas and implementations for the legacy-migration coordinator (Domain 1.7).

_list_modules/_analyze_module back the baseline investigation. _check_module_diff
backs the resume path — a targeted update for just the module that changed,
rather than re-running the baseline from scratch. _estimate_migration_effort
backs the fork path — two forked sessions asking about different strategies
get genuinely different effort/risk numbers from the same shared baseline.
The Anthropic-provided memory tool (memory_20250818, see memory_tool.py) backs
the restart path — a curated, explicitly-written/updated file the coordinator
can read back in a brand-new conversation instead of trusting replayed raw
tool results that may have gone stale.

The only export is TOOLS: a list of {"schema": ..., "implementation": ...}
entries. common/agent_loop.py extracts the schemas for the Anthropic API call
and builds its own name -> implementation map to dispatch tool_use blocks
directly — nothing else in this module needs to be imported elsewhere.
"""

from common.errors import tool_error

from data import CHANGES_SINCE_BASELINE, MIGRATION_ESTIMATES, MODULES
from memory_tool import memory_tool


def _list_modules() -> dict:
    return {
        "modules": [
            {"module": name, **{k: v for k, v in info.items() if k != "last_changed"}}
            for name, info in MODULES.items()
        ]
    }


def _analyze_module(module_name: str) -> dict:
    info = MODULES.get(module_name)
    if info is None:
        return tool_error("validation", False, f"No module named '{module_name}'.")
    return {"module": module_name, **info}


def _check_module_diff(module_name: str) -> dict:
    if module_name not in MODULES:
        return tool_error("validation", False, f"No module named '{module_name}'.")
    change = CHANGES_SINCE_BASELINE.get(module_name)
    return {
        "module": module_name,
        "changed_since_baseline": change is not None,
        "summary": change or "No recorded changes since the baseline analysis.",
    }


def _estimate_migration_effort(strategy: str, module_name: str) -> dict:
    estimate = MIGRATION_ESTIMATES.get((strategy, module_name))
    if estimate is None:
        return tool_error(
            "validation",
            False,
            f"No migration estimate for strategy '{strategy}' on module '{module_name}'. "
            "Known strategies: strangler-fig, big-bang.",
        )
    return {"strategy": strategy, "module": module_name, **estimate}


TOOLS = [
    {
        "schema": {
            "name": "list_modules",
            "description": (
                "List every module in the legacy monolith with its summary stats (lines of "
                "code, coupling score, test coverage). Use this FIRST when starting a fresh "
                "baseline investigation, before calling analyze_module on any module individually."
            ),
            "input_schema": {"type": "object", "properties": {}},
        },
        "implementation": _list_modules,
    },
    {
        "schema": {
            "name": "analyze_module",
            "description": (
                "Get the detailed stats for ONE named module (lines of code, coupling score, "
                "test coverage, last-changed date). Call this once per module you need to "
                "assess in depth during a baseline investigation."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"module_name": {"type": "string", "description": "e.g. 'billing'."}},
                "required": ["module_name"],
            },
        },
        "implementation": _analyze_module,
    },
    {
        "schema": {
            "name": "check_module_diff",
            "description": (
                "Check whether a specific module has changed since the baseline investigation, "
                "and what changed. Use this in a RESUMED session when told a particular module "
                "changed, instead of re-running list_modules or re-analyzing every module from "
                "scratch — this gives a targeted update for just that module."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"module_name": {"type": "string", "description": "e.g. 'billing'."}},
                "required": ["module_name"],
            },
        },
        "implementation": _check_module_diff,
    },
    {
        "schema": {
            "name": "estimate_migration_effort",
            "description": (
                "Estimate migration effort, timeline, and risk for one module under ONE named "
                "migration strategy ('strangler-fig' or 'big-bang'). Call this once you're "
                "comparing or recommending a specific strategy for a specific module."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "strategy": {"type": "string", "enum": ["strangler-fig", "big-bang"]},
                    "module_name": {"type": "string", "description": "e.g. 'billing'."},
                },
                "required": ["strategy", "module_name"],
            },
        },
        "implementation": _estimate_migration_effort,
    },
    {
        "schema": {"type": "memory_20250818", "name": "memory"},
        "implementation": memory_tool,
    },
]
