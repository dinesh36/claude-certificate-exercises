"""
Task 7: Session Resumption & Forking
Domain: 1 (Agentic Architecture & Orchestration) — Task Statement 1.7

A legacy-codebase migration coordinator that investigates a monolith's
modules as a baseline session, can be resumed later and told about one
specific module that changed (a targeted re-analysis rather than a full
re-exploration), can be forked from that shared baseline into independent
branches comparing divergent migration strategies, and can alternatively be
restarted with a genuinely empty conversation that recovers context from
Anthropic's memory tool instead of resuming or replaying anything — the
right choice when the raw session's tool results would otherwise be stale.

`new`/`resume`/`fork` are built on common/session_store.py (save/load/fork
of the actual prior messages — the --resume/fork_session mechanic). `restart`
is built on Anthropic's memory tool (memory_20250818, see memory_tool.py)
instead: it has no concept of a conversation transcript at all, so it can't
resume or fork anything — what it's good for is a curated, explicitly
written/updated file a brand-new session reads back, rather than a raw
tool-call history that might contain an outdated fact baked into an old
tool_result.

See data.py for the mock module/change/estimate data, tools.py for the tool
schemas/implementations, and common/session_store.py for the save/load/fork
primitives the resume/fork modes are built on.
"""

import sys

from common.agent_loop import run_tool_loop
from common.client import DEFAULT_MODEL, get_client
from common.session_store import fork_session, load_session, save_session
from memory_tool import reset_memory

from tools import TOOLS

client = get_client()

SYSTEM_PROMPT = (
    "You are a legacy-codebase migration coordinator. On a fresh baseline "
    "investigation, call list_modules first, then analyze_module for every "
    "module that needs a closer look, before summarizing coupling, "
    "complexity, and test-coverage risk. Once you've completed a baseline "
    "investigation, use your memory tool to record a concise summary of your "
    "findings — one line per module — in /memories/legacy-migration-baseline.md, "
    "so a later session can recover your findings without replaying every "
    "tool call. If you are told a specific module changed since your last "
    "analysis, call check_module_diff for that module, update your "
    "assessment for just that module, and update your memory file to keep it "
    "current — do not re-run list_modules or re-analyze modules that were "
    "not mentioned as changed. When asked to recommend or compare a specific "
    "migration strategy for a module, call estimate_migration_effort for "
    "that exact strategy/module pair before giving a recommendation."
)

DEFAULT_SESSION_ID = "legacy-migration-baseline"


def _run(message: str, history) -> list:
    result = run_tool_loop(
        client=client,
        model=DEFAULT_MODEL,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        user_message=message,
        history=history,
    )
    print(f"\nAgent: {result.final_text}")
    return result.messages


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "new"

    if mode == "new":
        session_id = DEFAULT_SESSION_ID
        message = (
            sys.argv[2]
            if len(sys.argv) > 2
            else (
                "Investigate the legacy monolith's modules (billing, auth, reporting) and "
                "summarize coupling, complexity, and test-coverage risk for each as a baseline "
                "for a future migration decision."
            )
        )
        reset_memory()
        print(f"[new session '{session_id}'] (memory cleared for a fresh baseline)\nUser: {message}")
        messages = _run(message, history=None)
        save_session(session_id, messages)

    elif mode == "resume":
        session_id = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SESSION_ID
        message = (
            sys.argv[3]
            if len(sys.argv) > 3
            else (
                "Since your last analysis, the billing module changed — check what's "
                "different and update your risk assessment for it specifically."
            )
        )
        history = load_session(session_id)
        if history is None:
            raise SystemExit(f"No saved session '{session_id}' to resume — run 'new' first.")
        print(f"[resuming session '{session_id}']\nUser: {message}")
        messages = _run(message, history=history)
        save_session(session_id, messages)

    elif mode == "fork":
        if len(sys.argv) < 4:
            raise SystemExit('Usage: main.py fork <source_session_id> <new_session_id> ["message"]')
        source_id, new_id = sys.argv[2], sys.argv[3]
        message = (
            sys.argv[4]
            if len(sys.argv) > 4
            else "Given the baseline, recommend a strangler-fig migration plan starting with the highest-risk module."
        )
        history = fork_session(source_id, new_id)
        print(f"[forked '{source_id}' -> '{new_id}']\nUser: {message}")
        messages = _run(message, history=history)
        save_session(new_id, messages)

    elif mode == "restart":
        session_id = sys.argv[2] if len(sys.argv) > 2 else "fresh-restart"
        message = (
            sys.argv[3]
            if len(sys.argv) > 3
            else (
                "Recommend a migration strategy for billing, with effort/timeline/risk — "
                "check your memory for anything already known before investigating further."
            )
        )
        print(
            f"[restarting '{session_id}' — empty conversation, recovering context from the "
            f"memory tool instead of resuming or replaying any prior transcript]\nUser: {message}"
        )
        messages = _run(message, history=None)
        save_session(session_id, messages)

    else:
        raise SystemExit(f"Unknown mode '{mode}'. Use: new | resume | fork | restart")
