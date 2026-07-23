# Task Statement 2.5: Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively
## Knowledge of
- Grep for content search (searching file contents for patterns like function names, error messages, or import statements)
- Glob for file path pattern matching (finding files by name or extension patterns)
- Read/Write for full file operations; Edit for targeted modifications using unique text matching
- When Edit fails due to non-unique text matches, using Read + Write as a fallback for reliable file modifications
## Skills in
- Selecting Grep for searching code content across a codebase (e.g., finding all callers of a function, locating error messages)
- Selecting Glob for finding files matching naming patterns (e.g., **/*.test.tsx)
- Using Read to load full file contents followed by Write when Edit cannot find unique anchor text
- Building codebase understanding incrementally: starting with Grep to find entry points, then using Read to follow imports and trace flows, rather than reading all files upfront
- Tracing function usage across wrapper modules by first identifying all exported names, then searching for each name across the codebase

---

# Subject
A small, real, working Python task-queue library (`core.py`, `compat.py`, `workers.py`, `config.py`, `cli.py`, plus tests). It's shaped specifically to make each built-in tool the natural choice: a function called from several files, a legacy alias module, files matching a test-naming pattern, and one deliberately duplicated config block.
- `enqueue_task` is defined once in `core.py` but called from `cli.py` and two test files — a real multi-file content search, not a single-file lookup.
- `compat.py` re-exports `enqueue_task`/`dequeue_task` under legacy names (`add_job`/`get_next_job`), so tracing usage means reading the wrapper first, then searching for the alias.
- `config.py`'s `RETRY_POLICIES` list holds three byte-for-byte identical dicts. Picking one out by position genuinely can't be done with a small `Edit` anchor — this is what forces the real Read + Write fallback documented below.

---

# How to verify
This task has no script to run — it's a small sample codebase. Open a Claude Code session with this folder as the working directory, then try:

**This folder logs every tool call for you.** `.claude/settings.json` wires a `PostToolUse` hook (`.claude/hooks/log_tool_use.py`) that fires on every tool call in any session opened here. It appends the tool name, its exact input, and its result to `logs/tool-selection/task-5-built-in-tool-selection.jsonl`, in this repo's usual pretty-printed log format. This is what actually backs every "live-verified" claim below — not a self-reported summary from the model, but a real, deterministic record written by Claude Code itself.

```
Find every place enqueue_task is called in this codebase — not where it's defined, and not the compat.py re-export line.
```
Should return four real call sites (`cli.py`, and both `enqueue_task` calls inside `tests/`), and exclude the definition, the docstring example, and every import/re-export line. **Live-verified caveat, straight from the hook's own log:** in a headless `claude -p` session, this generic phrasing gets answered by a Bash `grep` invocation, not the dedicated Grep tool — Grep exists but is a *deferred* tool here, discovered only when the model searches for it. Even asking explicitly ("use the Grep tool, not Bash grep") isn't reliable: one logged run found and used it after a `ToolSearch` call, another logged run of the exact same prompt ran five different `ToolSearch` queries, never found it, and fell back to Bash `grep` anyway. Either way, the actual reasoning bullet this tests — telling a real call from a definition, docstring example, or import — was correct in every logged run.

```
List every test file in this project.
```
Should return exactly `tests/test_cli.py`, `tests/test_config.py`, `tests/test_core.py`, `tests/test_workers.py`. Same caveat as above: unprompted, this defaulted to a Bash `find` call rather than Glob, for the same deferred-tool reason.

```
Fix the docstring typo in core.py's enqueue_task function: 'serializeable' should be 'serializable'.
```
Should route to a single, clean `Edit` call with a unique anchor. Live-verified: this worked on the first attempt, no fallback needed.

```
In config.py, RETRY_POLICIES[1] (the middle entry) should back off for 10 seconds instead of 5. Indexes 0 and 2 must stay at 5.
```
All three list entries are currently identical, so there's no small snippet of text that appears only in entry 1. Live-verified: a well-context-widened `Edit` call (one that includes the whole tail of the list up to the closing `]`) can still succeed in one shot — Claude is good at finding *some* unique anchor before giving up. To see the actual failure mode this bullet is about, try a deliberately narrow edit instead:
```
Edit config.py and change just one policy dict's max_attempts to 5, using only that dict's own four lines as the anchor text.
```
This fails for real, with: `Found 2 matches of the string to replace, but replace_all is false. To replace all occurrences, set replace_all to true. To replace only one occurrence, please provide more context to uniquely identify the instance.` The correct recovery — confirmed live — is Read the full file, then Write it back with only the intended occurrence changed.

```
Trace how the legacy name add_job flows through this codebase — where is it defined, and who actually calls it?
```
Should Read `compat.py` first to learn `add_job` is just `core.enqueue_task` re-exported, then search for `add_job` itself, landing on its one real call site in `cli.py`.

```
Start from cli.py and explain what this program does end to end, tracing its imports as you go.
```
Should read `cli.py` first, then follow its imports one at a time (`compat.py` → `core.py` → `workers.py` → `config.py`) — not read every file in the folder upfront. Live-verified: the session read exactly those four files and never touched `tests/`, since nothing in `cli.py`'s import chain needed it.

---

# Implementation Info
> `core.py`/`compat.py`/`workers.py`/`config.py`/`cli.py` form one small, real, tested task-queue library. `tests/` holds one test file per module. `.claude/settings.json` and `.claude/hooks/log_tool_use.py` log every tool call a live session makes here. Nothing in this task is an MCP server or an Anthropic API script — the codebase itself is the graded artifact, exercised by a live Claude Code session.

**How the tool-call logging works** — `.claude/settings.json`, `.claude/hooks/log_tool_use.py`

```json
{
  "hooks": {
    "PostToolUse": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "uv run python3 .claude/hooks/log_tool_use.py" }] }
    ]
  }
}
```
```python
payload = json.load(sys.stdin)
record = {
    "session_id": payload.get("session_id"),
    "tool_name": payload.get("tool_name"),
    "tool_input": payload.get("tool_input"),
    "tool_response": payload.get("tool_response"),
}
append_log(record, repo_root / "logs" / "tool-selection" / "task-5-built-in-tool-selection.jsonl")
```
Claude Code invokes this script after every tool call in any session opened in this folder, passing the tool's name, input, and result as JSON on stdin. The hook reuses `common/logging_utils.py`'s `append_log` — the same pretty-printed, formatted-JSON shape every other task's logging already uses — so every "live-verified" claim in this README traces back to a real, inspectable log entry instead of a self-reported summary.

## How each Task Info item is covered:
- **Grep for content search (searching file contents for patterns like function names, error messages, or import statements)** — `core.py`, `cli.py`, `tests/test_core.py`, `tests/test_workers.py`

  ```python
  # core.py
  def enqueue_task(name: str, payload: dict) -> None:
      ...

  # cli.py
  from core import enqueue_task
  ...
  enqueue_task("build_report", {"report": "weekly-summary"})
  ```

  `enqueue_task` has a real definition and four real call sites spread across three files, plus a docstring example and an import line that both look similar but aren't calls. Finding just the real calls requires a content search across the whole codebase, not a single-file read.

- **Glob for file path pattern matching (finding files by name or extension patterns)** — `tests/`

  ```
  tests/test_cli.py
  tests/test_config.py
  tests/test_core.py
  tests/test_workers.py
  ```

  All four test files share the `test_*.py` naming convention, distinct from every other file in the folder — the kind of name-pattern match Glob is for, rather than a content search.

- **Read/Write for full file operations; Edit for targeted modifications using unique text matching** — `core.py`

  ```python
  """Add a job to the queue. `payload` is any JSON-serializeable dict.
  ```

  This docstring typo appears exactly once in the whole codebase. Live-verified: a single `Edit` call with that line as the anchor fixed it cleanly on the first attempt.

- **When Edit fails due to non-unique text matches, using Read + Write as a fallback for reliable file modifications** — `config.py`

  ```python
  RETRY_POLICIES = [
      {
          "max_attempts": 3,
          "backoff_seconds": 5,
          "log_message": "retrying job",
      },
      {
          "max_attempts": 3,
          "backoff_seconds": 5,
          "log_message": "retrying job",
      },
      {
          "max_attempts": 3,
          "backoff_seconds": 5,
          "log_message": "retrying job",
      },
  ]
  ```

  Live-verified: attempting to `Edit` one dict using only its own four lines as the anchor fails with `Found 2 matches of the string to replace, but replace_all is false...`. The real fix was Read the full file, then Write it back with only the intended entry changed — the exact fallback this bullet describes.

- **Selecting Grep for searching code content across a codebase (e.g., finding all callers of a function, locating error messages)** — `.claude/hooks/log_tool_use.py`'s captured log

  ```json
  {
    "tool_name": "Bash",
    "tool_input": {
      "command": "grep -rn \"enqueue_task\" .../task-5-built-in-tool-selection --include=\"*.py\""
    }
  }
  ```

  Straight from `logs/tool-selection/task-5-built-in-tool-selection.jsonl`: asked generically, the search ran as Bash `grep`, since Grep is a deferred tool here and isn't loaded by default. Asked explicitly to use the Grep tool, one logged run found it via `ToolSearch` and called it directly; another logged run of the identical prompt burned five separate `ToolSearch` queries, never found it, and fell back to Bash `grep` anyway — tool *availability* itself isn't fully deterministic in this environment. The reasoning this bullet is actually about — correctly excluding the definition, docstring example, and import lines — was right in every logged run regardless of which literal tool executed the search.

- **Selecting Glob for finding files matching naming patterns (e.g., **/*.test.tsx)** — `tests/` directory listing

  Same caveat as the Grep bullet: unprompted, this environment defaulted to Bash `find -iname "*test*"` rather than Glob. The naming-pattern reasoning itself (that all four files share the `test_*.py` shape) was correct in every run.

- **Using Read to load full file contents followed by Write when Edit cannot find unique anchor text** — `config.py`

  Same transcript as the Edit-fallback bullet above: `Read` returned the full file, and the fix was applied with `Write`, not a second narrower `Edit` attempt.

- **Building codebase understanding incrementally: starting with Grep to find entry points, then using Read to follow imports and trace flows, rather than reading all files upfront** — `cli.py`

  ```python
  """Command-line entry point for the task-queue demo."""

  from compat import add_job
  from core import enqueue_task
  from workers import process_email_job, process_report_job
  ```

  Live-verified: given "start from cli.py and explain what this program does," the session read `cli.py`, then `compat.py`, `core.py`, `workers.py`, and `config.py` in that order — following the actual import chain — and never opened `tests/` at all, since nothing in the chain needed it.

- **Tracing function usage across wrapper modules by first identifying all exported names, then searching for each name across the codebase** — `compat.py`

  ```python
  """Legacy aliases for core.py, kept for callers who haven't migrated to the new names yet.

  Do not add new functionality here — this module only re-exports.
  """

  from core import enqueue_task as add_job
  from core import dequeue_task as get_next_job
  ```

  Live-verified: asked to trace `add_job`, the session read `compat.py` first to learn it's an alias for `core.enqueue_task`, then searched for `add_job` itself and correctly found its one real call site in `cli.py` — and correctly reported that `get_next_job` (the other alias) has zero callers anywhere in the codebase.
