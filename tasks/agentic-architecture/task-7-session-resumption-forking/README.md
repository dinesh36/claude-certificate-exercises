# Task Statement 1.7: Manage session state, resumption, and forking
## Knowledge of
- Named session resumption using --resume to continue a specific prior conversation
- fork_session for creating independent branches from a shared analysis baseline to explore divergent approaches
- The importance of informing the agent about changes to previously analyzed files when resuming sessions after code modifications
- Why starting a new session with a structured summary is more reliable than resuming with stale tool results
## Skills in
- Using --resume with session names to continue named investigation sessions across work sessions
- Using fork_session to create parallel exploration branches (e.g., comparing two testing strategies or refactoring approaches from a shared codebase analysis)
- Choosing between session resumption (when prior context is mostly valid) and starting fresh with injected summaries (when prior tool results are stale)
- Informing a resumed session about specific file changes for targeted re-analysis rather than requiring full re-exploration

---

# Subject
A legacy-codebase migration coordinator that investigates a monolith's modules (`billing`, `auth`, `reporting`) as a named baseline session. It then demonstrates every way that session can continue:
- Resumed later, with a targeted note about one module that changed.
- Forked into independent branches comparing divergent migration strategies from the same shared baseline.
- Abandoned for a genuinely empty conversation that recovers context from Anthropic's memory tool, instead of replaying stale tool results.

How the pieces fit together:
- `new`/`resume`/`fork` are built on `common/session_store.py`, a small reusable primitive (`save_session`/`load_session`/`fork_session`) that persists and replays the actual prior conversation — the real `--resume`/`fork_session` mechanic.
- `restart` is built on Anthropic's built-in memory tool (`memory_20250818`, see `memory_tool.py`) instead. This is a genuinely different mechanism, with no concept of a conversation transcript at all, so it can't resume or fork anything. The coordinator writes a curated findings file to `/memories` during the baseline and keeps it current on `resume`. `restart` starts a brand-new, empty conversation and recovers context by reading that file back, rather than trusting a raw tool result that may have gone stale.
- Resuming after `billing`'s coupling score changed produces a **targeted** re-analysis of just that module, and updates the memory file to match. Forking the baseline into a strangler-fig branch and a big-bang branch produces genuinely different effort/risk recommendations from identical starting context.

---

# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run tasks/agentic-architecture/task-7-session-resumption-forking/main.py new
```
This starts and saves a fresh baseline session (`legacy-migration-baseline`) investigating all three modules. It also clears the memory directory first, so a second `new` run starts with a genuinely clean slate — otherwise the coordinator's `create` call would fail with "File already exists" against a leftover file from a previous run. Then try each continuation mode against that saved session:
```bash
uv run tasks/agentic-architecture/task-7-session-resumption-forking/main.py resume
```
Resumes `legacy-migration-baseline` and tells it `billing` changed since the baseline. The agent calls `check_module_diff("billing")` and updates only billing's assessment, leaving `auth` and `reporting` untouched, rather than re-running the whole investigation.
```bash
uv run tasks/agentic-architecture/task-7-session-resumption-forking/main.py fork legacy-migration-baseline branch-strangler "Recommend a strangler-fig migration plan for billing, with effort/timeline/risk."
uv run tasks/agentic-architecture/task-7-session-resumption-forking/main.py fork legacy-migration-baseline branch-bigbang "Recommend a big-bang rewrite plan for billing, with effort/timeline/risk."
```
Both forks start from the identical saved baseline, but diverge: one gets a ~10-week low-risk incremental plan, the other a ~4-week high-risk rewrite plan. This proves the fork is a real independent branch, not a shared mutable session.
```bash
uv run tasks/agentic-architecture/task-7-session-resumption-forking/main.py restart
```
Starts a genuinely empty conversation — no saved session, no seeded history at all — with only the memory tool attached. The API auto-injects an instruction to check `/memories` before doing anything else.

So the coordinator reads back the findings file `new`/`resume` wrote and updated, and recommends a migration strategy for billing from that *current* picture (coupling now 3, not the original 8) — without replaying a single raw tool result from the baseline session.

---

# Implementation Info
> A legacy-migration coordinator split across `data.py` (mock module/change/estimate data), `tools.py` (tool schemas/implementations, including the built-in memory tool's registration), `memory_tool.py` (the client-side handler for Anthropic's `memory_20250818` tool), and `main.py` (four session modes + entry point) — built on a new `common/session_store.py` primitive (`save_session`/`load_session`/`fork_session`) and a `history` parameter added to `common/agent_loop.py`'s `run_tool_loop`.
## How each Task Info item is covered:
- **Named session resumption using --resume to continue a specific prior conversation** — `main.py`, `common/session_store.py`

  ```python
  elif mode == "resume":
      session_id = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SESSION_ID
      ...
      history = load_session(session_id)
      if history is None:
          raise SystemExit(f"No saved session '{session_id}' to resume — run 'new' first.")
  ```

  `resume` mode takes a named session id, loads its saved history via `load_session`, and continues the same conversation. This is the equivalent of `--resume <name>` for this task's own session mechanism.

- **fork_session for creating independent branches from a shared analysis baseline to explore divergent approaches** — `common/session_store.py`

  ```python
  def fork_session(source_session_id: str, new_session_id: str) -> list:
      history = load_session(source_session_id)
      if history is None:
          raise ValueError(f"No saved session '{source_session_id}' to fork from.")
      save_session(new_session_id, history)
      return history
  ```

  `fork_session` copies the source session's history into a brand-new session id, persisted immediately. The original baseline stays untouched while the new branch continues independently.

- **The importance of informing the agent about changes to previously analyzed files when resuming sessions after code modifications** — `main.py`

  ```python
  message = (
      sys.argv[3]
      if len(sys.argv) > 3
      else (
          "Since your last analysis, the billing module changed — check what's "
          "different and update your risk assessment for it specifically."
      )
  )
  ```

  The resume prompt explicitly names which module changed, rather than silently resuming and hoping the model notices. Verified live: the agent called `check_module_diff("billing")` and revised only billing's risk tier, explicitly noting `auth` and `reporting` were unaffected.

- **Why starting a new session with a structured summary is more reliable than resuming with stale tool results** — `main.py`, `memory_tool.py`

  ```python
  print(
      f"[restarting '{session_id}' — empty conversation, recovering context from the "
      f"memory tool instead of resuming or replaying any prior transcript]\nUser: {message}"
  )
  messages = _run(message, history=None)
  ```

  `restart` mode passes `history=None` — a genuinely empty conversation, not a seeded fake one — and relies entirely on the memory tool to recover context.

  Verified live: after `resume` updated `/memories/legacy-migration-baseline.md` to say billing's coupling dropped from 8 to 3, a `restart` run with zero history correctly recommended a strategy based on the *current* picture (coupling 3). There is no replayed transcript at all, so it can't be trusting a stale `analyze_module` tool result baked into one.

  Note: `new` mode calls `reset_memory()` first (see `memory_tool.py`). Only `new` clears the memory directory — `restart` never does, since recovering whatever is already there is its entire purpose.

- **Using --resume with session names to continue named investigation sessions across work sessions** — `main.py`, `common/session_store.py`

  ```python
  history = load_session(session_id)
  ...
  messages = _run(message, history=history)
  save_session(session_id, messages)
  ```

  Every `resume` call re-saves the session under the same name after continuing it. A later `resume` call picks up exactly where this one left off — a real multi-call, named investigation, not a single-shot conversation.

- **Using fork_session to create parallel exploration branches (e.g., comparing two testing strategies or refactoring approaches from a shared codebase analysis)** — `main.py`, `tools.py`

  ```python
  {
      "schema": {
          "name": "estimate_migration_effort",
          "description": (
              "Estimate migration effort, timeline, and risk for one module under ONE named "
              "migration strategy ('strangler-fig' or 'big-bang')."
          ),
          ...
      },
      "implementation": _estimate_migration_effort,
  },
  ```

  `branch-strangler` and `branch-bigbang` fork the identical baseline, then each call `estimate_migration_effort` with a different `strategy` argument. Verified live: the two branches returned genuinely different effort/risk profiles (~10 weeks/low risk vs. ~4 weeks/high risk) for the same module, from the same shared starting context.

- **Choosing between session resumption (when prior context is mostly valid) and starting fresh with injected summaries (when prior tool results are stale)** — `main.py`, `tools.py`

  ```python
  {
      "schema": {"type": "memory_20250818", "name": "memory"},
      "implementation": memory_tool,
  },
  ```

  `resume` and `restart` are genuinely different mechanisms living side by side in the same `TOOLS` list.

  `resume` (via `common/session_store.py`) is the right choice when most of the baseline still holds. It replays the actual prior messages, so it's cheap and preserves everything still valid.

  `restart` (via the memory tool) is the right choice when the raw history itself would mislead the model. It never sees the old messages at all — only whatever curated fact was explicitly written or updated.

  The task's "How to run" section walks through both, so the tradeoff is directly comparable.

- **Informing a resumed session about specific file changes for targeted re-analysis rather than requiring full re-exploration** — `tools.py`, `main.py`

  ```python
  "description": (
      "Check whether a specific module has changed since the baseline investigation, "
      "and what changed. Use this in a RESUMED session when told a particular module "
      "changed, instead of re-running list_modules or re-analyzing every module from "
      "scratch — this gives a targeted update for just that module."
  ),
  ```

  `check_module_diff`'s own description, reinforced by the system prompt's "do not re-run list_modules or re-analyze modules that were not mentioned as changed," is what kept the resumed session's re-analysis scoped to `billing` alone. Verified live in the resume run above.
