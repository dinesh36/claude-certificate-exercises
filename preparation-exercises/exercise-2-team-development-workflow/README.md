# Preparation Exercise 2: Configure Claude Code for a Team Development Workflow

**Objective:** Practice configuring CLAUDE.md hierarchies, custom slash commands, path-specific rules, and MCP server integration for a multi-developer project.

**Steps:**
1. Create a project-level CLAUDE.md with universal coding standards and testing conventions. Verify that instructions placed at the project level are consistently applied across all team members.
2. Create .claude/rules/ files with YAML frontmatter glob patterns for different code areas (e.g., paths: ["src/api/**/*"] for API conventions, paths: ["**/*.test.*"] for testing conventions). Test that rules load only when editing matching files.
3. Create a project-scoped skill in .claude/skills/ with context: fork and allowed-tools restrictions. Verify the skill runs in isolation without polluting the main conversation context.
4. Configure an MCP server in .mcp.json with environment variable expansion for credentials. Add a personal experimental MCP server in ~/.claude.json and verify both are available simultaneously.
5. Test plan mode versus direct execution on tasks of varying complexity: a single-file bug fix, a multi-file library migration, and a new feature with multiple valid implementation approaches. Observe when plan mode provides value.

---

# Subject

A multiplayer game backend monorepo — `matchmaking_service/`, `leaderboard_service/`, and a `shared_protocol/` package both services import from — used to demonstrate the full Claude Code configuration hierarchy plus a live plan-mode judgment call.

- Steps 1-3 and 5 are one sample project, verified via documented prompts and a `PostToolUse` hook. Step 4 is a real MCP server (`game-ops`), verified by registering it with a live Claude Code session.

---

# How to run / verify

This exercise has no top-level script to `uv run` for Steps 1, 2, 3, and 5 — they're Claude Code configuration and a live session's own judgment. Step 4 is a real MCP server.

**Verification status:** the Anthropic API key backing this environment is currently out of credit, so the prompts below haven't been driven through a live/headless `claude` session yet — `claude -p` fails with the same credit error for both a live-session prompt and the `.mcp.json` approval flow. What *has* been verified directly: every Python module's logic (`find_match`, `submit_match_result`'s idempotency, the `format_rank_label` bug reproducing as `#0` instead of `#1`), `server.py`'s tool signatures surviving the `logged_tool` decorator, and the MCP registration mechanics themselves — `claude mcp list` correctly shows `game-ops` as `⏸ Pending approval` (project scope, matching the documented behavior) with a `Missing environment variables: GAMEOPS_API_KEY` warning when the key isn't exported. Re-run the prompts below once credits are available, rather than trusting this note as a substitute.

## Steps 1, 2, 3, 5 — open a session here

Open a Claude Code session with this folder (`preparation-exercises/exercise-2-team-development-workflow/`) as the working directory. `.claude/settings.json` wires a `PostToolUse` hook that logs every tool call to `logs/preparation-exercises/exercise-2-team-development-workflow.jsonl` — every claim below is backed by that log.

```
/memory
```
Expected: lists this folder's own `CLAUDE.md`, plus `matchmaking_service/CLAUDE.md` or `leaderboard_service/CLAUDE.md` if your session's context has touched either — confirming the project-level file applies everywhere while each service's file only layers in for that service (Step 1).

```
What's the leaderboard_service's rule about handling duplicate score submissions?
```
Expected: cites `leaderboard_service/CLAUDE.md`'s idempotency rule and `.claude/rules/testing-conventions.md`'s duplicate-submission test requirement — the latter only loads because the answer involves a file under `tests/` (Step 2).

```
Draft patch notes for the recent changes to this monorepo.
```
Expected: dispatches the `patch-notes-draft` skill in a forked context — the skill's own `git diff`/`git log` exploration doesn't clutter the main conversation, and the draft groups by service in plain language, not by file or internal function name (Step 3).

```
leaderboard's rank display is off — the #1 player is showing as #0. Fix it.
```
Expected: direct execution, no `EnterPlanMode` call — a single-line fix in `leaderboard_service/leaderboard.py`'s `format_rank_label` (Step 5, simple).

```
We need to migrate Player.player_id from an int to a UUID string across shared_protocol, matchmaking_service, and leaderboard_service — including the leaderboard's score dict, which is currently keyed by player_id.
```
Expected: an `EnterPlanMode` call before any edits — this touches 3 packages and has more than one valid approach (hard cutover vs. a translation shim) (Step 5, architectural).

```
We're retiring LegacyMatchmakingQueue. Find every place it's still referenced before we remove it.
```
Expected: an `Agent` call with `subagent_type: Explore` (or, at this codebase's small size, a direct `Grep` sweep — both are legitimate, scale-dependent choices; see `tasks/claude-code-workflows/task-4-plan-mode-vs-direct-execution/README.md` for the same tradeoff at a similarly small scale). Either way it should find both real references: `matchmaker.py`'s `enqueue_for_legacy_review` and `queue_worker.py`'s `flush_legacy_queue` (Step 5, discovery).

## Step 4 — the MCP server

`game-ops` is registered at **project** scope via this folder's own `.mcp.json` (committed) — unlike local scope, there's no separate `claude mcp add` step. It takes effect automatically the first time a Claude Code session's working directory is exactly this folder, pending one-time approval.

```bash
cd preparation-exercises/exercise-2-team-development-workflow
export GAMEOPS_API_KEY=some-test-value
```
Start a normal `claude` session from this folder — Claude Code prompts to approve the new `.mcp.json` server the first time. Then:
```bash
claude mcp list
```
`game-ops` should at least appear. Project scope's status column isn't reliable proof either way (it can show `⏸ Pending approval` even once the server's tools work) — the real check is a live prompt. From a live session in this folder:
```
What incidents are currently open in eu-west?
```
Expected: calls `list_active_incidents`, returns the matchmaking-latency incident, not the resolved leaderboard one.
```
What's the status of SRV-1002?
```
Expected: calls `get_server_status`, returns `degraded` — the exact server named, not a browse/list call.

For the personal/experimental angle, register a second copy at **user** scope and confirm it's available from an unrelated directory:
```bash
claude mcp add --scope user --transport stdio game-ops-personal-demo -- uv run --directory "$(pwd)" server.py
cd /tmp
claude mcp list
```
Expected: `game-ops-personal-demo` appears here too, `✔ Connected` — even though `/tmp` has nothing to do with this repo. Clean up afterward since a user-scoped server follows you into every project:
```bash
claude mcp remove --scope user game-ops-personal-demo
```

---

# Implementation Info

> `CLAUDE.md` (root, `matchmaking_service/`, `leaderboard_service/`) is the project/directory-level hierarchy. `.claude/rules/*.md` are the path-scoped rules. `.claude/skills/patch-notes-draft/` is the project-scoped skill. `server.py`/`data.py`/`.mcp.json` are the MCP server. `.claude/settings.json`/`.claude/hooks/log_tool_use.py` log every tool call for verification.

## How each Step is covered:

- **Step 1 — Create a project-level CLAUDE.md with universal coding standards and testing conventions; verify project-level instructions are consistently applied across team members** — `CLAUDE.md`

  ```
  ## Coding standards
  - Python 3.11+, full type hints on every public function.
  - Prefer `dataclasses` for shared data shapes (see `shared_protocol/types.py`) over bare dicts.
  - No service imports another service directly — shared shapes only ever live in `shared_protocol/`.

  ## Testing conventions
  - Every package has its own `tests/` directory, run with `pytest`.
  ```

  This is the sample project's own root config, at the top of the hierarchy every service's directory-level `CLAUDE.md` builds on. `/memory` confirms it loads regardless of which service you're working in.

- **Step 2 — Create `.claude/rules/` files with YAML frontmatter glob patterns for different code areas; verify rules load only when editing matching files** — `.claude/rules/matchmaking-conventions.md`, `.claude/rules/testing-conventions.md`

  ```yaml
  ---
  paths:
    - "matchmaking_service/**"
  ---
  ```
  ```yaml
  ---
  paths:
    - "**/tests/**"
  ---
  ```

  One rule is scoped to a single service's own directory; the other is scoped by file pattern across every service — the two example shapes the exercise's own Step 2 text names (`src/api/**/*`-style vs. `**/*.test.*`-style).

- **Step 3 — Create a project-scoped skill in `.claude/skills/` with `context: fork` and `allowed-tools` restrictions; verify it runs in isolation without polluting the main conversation** — `.claude/skills/patch-notes-draft/SKILL.md`

  ```yaml
  ---
  name: patch-notes-draft
  description: Draft player-facing patch notes from the working tree's recent changes. Use when asked to draft, write, or summarize patch notes or changelog entries for a game update.
  context: fork
  allowed-tools: Read, Grep, Bash
  ---
  ```

  `context: fork` keeps the skill's own `git diff`/`git log` exploration out of the main conversation; `allowed-tools` restricts it to read-only inspection plus `Bash` for git commands — it can't edit or commit anything.

- **Step 4 — Configure an MCP server in `.mcp.json` with environment variable expansion for credentials; add a personal experimental MCP server in `~/.claude.json` and verify both are available simultaneously** — `.mcp.json`, `server.py`

  ```json
  {
    "mcpServers": {
      "game-ops": {
        "type": "stdio",
        "command": "uv",
        "args": ["run", "server.py"],
        "env": { "GAMEOPS_API_KEY": "${GAMEOPS_API_KEY}" }
      }
    }
  }
  ```

  `.mcp.json` only ever stores the `${GAMEOPS_API_KEY}` reference, never a real value — `server.py`'s `_require_api_key` rejects both a missing key and the literal unexpanded `${GAMEOPS_API_KEY}` text Claude Code passes through when the variable isn't set. The user-scope registration in "How to run / verify" above demonstrates the personal/experimental server living in `~/.claude.json`, available from any directory rather than just this one.

- **Step 5 — Test plan mode versus direct execution on tasks of varying complexity: a single-file bug fix, a multi-file library migration, and a new feature with multiple valid implementation approaches** — `leaderboard_service/leaderboard.py`, `shared_protocol/types.py`, `matchmaking_service/matchmaker.py`

  ```python
  def format_rank_label(rank_index: int) -> str:
      """Return a display label like '#1' for the given zero-based rank index."""
      return f"#{rank_index}"
  ```

  The rank-label bug is a genuine one-line fix (missing `+ 1`) — direct execution. The `Player.player_id` int-to-UUID migration spans `shared_protocol/types.py` plus both services' code that keys off `player_id` (including `leaderboard_service`'s `_scores` dict) — a real multi-file, cross-package change with more than one valid approach. `LegacyMatchmakingQueue`'s two call sites (`matchmaker.py`, `queue_worker.py`) make the discovery prompt a genuine multi-file search, not a single-file lookup.
