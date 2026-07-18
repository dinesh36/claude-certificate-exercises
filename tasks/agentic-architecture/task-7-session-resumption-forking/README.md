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
A legacy-codebase migration coordinator that investigates a monolith's modules (`billing`, `auth`, `reporting`) as a named baseline session, then demonstrates every way that session can continue: resumed later with a targeted note about one module that changed, forked into independent branches comparing divergent migration strategies from the same shared baseline, or abandoned in favor of a fresh session seeded with a structured summary instead of replaying stale tool results.
- `main.py` has four modes — `new`, `resume`, `fork`, `restart` — each backed by `common/session_store.py`, a small reusable primitive (`save_session`/`load_session`/`fork_session`) added to `common/` for this task.
- Resuming after `billing`'s coupling score changed produces a **targeted** re-analysis of just that module; forking the baseline into a strangler-fig branch and a big-bang branch produces genuinely different effort/risk recommendations from identical starting context.

---

# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run tasks/agentic-architecture/task-7-session-resumption-forking/main.py new
```
This starts and saves a fresh baseline session (`legacy-migration-baseline`) investigating all three modules. Then try each continuation mode against that saved session:
```bash
uv run tasks/agentic-architecture/task-7-session-resumption-forking/main.py resume
```
Resumes `legacy-migration-baseline` and tells it `billing` changed since the baseline — the agent calls `check_module_diff("billing")` and updates only billing's assessment, leaving `auth` and `reporting` untouched rather than re-running the whole investigation.
```bash
uv run tasks/agentic-architecture/task-7-session-resumption-forking/main.py fork legacy-migration-baseline branch-strangler "Recommend a strangler-fig migration plan for billing, with effort/timeline/risk."
uv run tasks/agentic-architecture/task-7-session-resumption-forking/main.py fork legacy-migration-baseline branch-bigbang "Recommend a big-bang rewrite plan for billing, with effort/timeline/risk."
```
Both forks start from the identical saved baseline but diverge — one gets a ~10-week low-risk incremental plan, the other a ~4-week high-risk rewrite plan — proving the fork is a real independent branch, not a shared mutable session.
```bash
uv run tasks/agentic-architecture/task-7-session-resumption-forking/main.py restart fresh-restart "billing's coupling dropped from 8 to 3 after the invoicing extraction, but test coverage is still only 22%" "Given that summary, recommend a migration strategy for billing with effort/timeline/risk."
```
Ignores the saved baseline entirely and seeds a brand-new session with a short structured summary instead — useful when the raw session's tool results (e.g. billing's original `coupling_score: 8`) would otherwise be replayed as stale context.

---

# Implementation Info
> A legacy-migration coordinator split across `data.py` (mock module/change/estimate data), `tools.py` (tool schemas/implementations), and `main.py` (four session modes + entry point), built on a new `common/session_store.py` primitive (`save_session`/`load_session`/`fork_session`) and a `history` parameter added to `common/agent_loop.py`'s `run_tool_loop`.
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

  `resume` mode takes a named session id, loads its saved history via `load_session`, and continues the same conversation — the equivalent of `--resume <name>` for this task's own session mechanism.

- **fork_session for creating independent branches from a shared analysis baseline to explore divergent approaches** — `common/session_store.py`

  ```python
  def fork_session(source_session_id: str, new_session_id: str) -> list:
      history = load_session(source_session_id)
      if history is None:
          raise ValueError(f"No saved session '{source_session_id}' to fork from.")
      save_session(new_session_id, history)
      return history
  ```

  `fork_session` copies the source session's history into a brand-new session id, persisted immediately — the original baseline stays untouched while the new branch continues independently.

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

  The resume prompt explicitly names which module changed rather than silently resuming and hoping the model notices — verified live: the agent called `check_module_diff("billing")` and revised only billing's risk tier, explicitly noting `auth` and `reporting` were unaffected.

- **Why starting a new session with a structured summary is more reliable than resuming with stale tool results** — `main.py`

  ```python
  seeded_history = [
      {
          "role": "user",
          "content": f"Structured summary of a prior investigation (treat this as current, not stale): {summary}",
      },
      {
          "role": "assistant",
          "content": "Understood — I'll treat that summary as the current state rather than re-deriving it from scratch.",
      },
  ]
  ```

  `restart` mode seeds a fresh session with a short, explicitly-current summary instead of replaying the baseline's original `analyze_module("billing")` tool result (which still shows the pre-extraction `coupling_score: 8`) — avoiding the risk of the model trusting stale tool output over the (correct) narrative summary.

- **Using --resume with session names to continue named investigation sessions across work sessions** — `main.py`, `common/session_store.py`

  ```python
  history = load_session(session_id)
  ...
  messages = _run(message, history=history)
  save_session(session_id, messages)
  ```

  Every `resume` call re-saves the session under the same name after continuing it, so a later `resume` call picks up exactly where this one left off — a real multi-call, named investigation rather than a single-shot conversation.

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

  `branch-strangler` and `branch-bigbang` fork the identical baseline and each call `estimate_migration_effort` with a different `strategy` argument — verified live: the two branches returned genuinely different effort/risk profiles (~10 weeks/low risk vs. ~4 weeks/high risk) for the same module, from the same shared starting context.

- **Choosing between session resumption (when prior context is mostly valid) and starting fresh with injected summaries (when prior tool results are stale)** — `main.py`

  Both `resume` and `restart` modes exist side by side in the same script rather than one replacing the other: `resume` is the right choice when most of the baseline still holds (only `billing` changed, `auth`/`reporting` are still valid), while `restart` is the right choice when the raw history itself would mislead the model (a stale `analyze_module` tool result outranking a corrected summary in the model's context). The task's "How to run" section walks through both so the tradeoff is directly comparable.

- **Informing a resumed session about specific file changes for targeted re-analysis rather than requiring full re-exploration** — `tools.py`, `main.py`

  ```python
  "description": (
      "Check whether a specific module has changed since the baseline investigation, "
      "and what changed. Use this in a RESUMED session when told a particular module "
      "changed, instead of re-running list_modules or re-analyzing every module from "
      "scratch — this gives a targeted update for just that module."
  ),
  ```

  `check_module_diff`'s own description — reinforced by the system prompt's "do not re-run list_modules or re-analyze modules that were not mentioned as changed" — is what kept the resumed session's re-analysis scoped to `billing` alone, verified live in the resume run above.
