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
A small, real, working Python task-queue library (`core.py`, `compat.py`, `workers.py`, `config.py`, `cli.py`, plus tests). It's shaped to make each built-in tool the natural choice.
- `enqueue_task` is called from several files — a real multi-file content search.
- `compat.py` re-exports `enqueue_task`/`dequeue_task` under legacy names, so tracing usage means reading the wrapper first, then searching for the alias.
- `config.py`'s `RETRY_POLICIES` list holds three identical dicts, testing whether a small `Edit` anchor can tell them apart.
- `stats.py` doesn't exist yet — asking for it is the clean way to see `Write` used for a brand-new file, since `Edit` can't touch a file that isn't there.

---

# How to verify
This task has no script to run — it's a small sample codebase. Open a Claude Code session with this folder as the working directory, then try the prompts below.

`.claude/settings.json` wires a `PostToolUse` hook (`.claude/hooks/log_tool_use.py`) that logs every tool call — name, input, result — to `logs/tool-selection/task-5-built-in-tool-selection.jsonl`. Every claim below is backed by that log, not a self-reported summary.

```
Find every place enqueue_task is called in this codebase — not where it's defined, and not the compat.py re-export line.
```
Expected: four real call sites (`cli.py`, and two in `tests/`), excluding the definition, docstring example, and import lines. In this environment, Grep is a deferred tool, so this generic phrasing gets answered by Bash `grep` instead. Even asking explicitly for the Grep tool is unreliable — one run found it via `ToolSearch`, another burned five `ToolSearch` queries and never did. The exclusion reasoning was correct in every run regardless of which tool executed the search.

```
List every test file in this project.
```
Expected: `tests/test_cli.py`, `tests/test_config.py`, `tests/test_core.py`, `tests/test_workers.py`. Glob is absent here, not just deferred — `ToolSearch` for `select:Glob` returns `No matching deferred tools found`. Every run defaults to Bash `find`. A standard interactive Claude Code session (not this sandbox's headless mode) has Glob as a first-class tool and should route here directly.

```
Fix the docstring typo in core.py's enqueue_task function: 'serializeable' should be 'serializable'.
```
Expected: a single, clean `Edit` call with a unique anchor.

```
The observability side of this queue is thin. Add a small stats.py module with a current_queue_depth() function that reuses core.queue_size(), plus a matching test file following the existing tests' style.
```
Expected: two `Write` calls, one per new file — `stats.py` and `tests/test_stats.py` don't exist yet, so `Edit` isn't an option. Delete both files afterward so the next person gets the same clean starting point.

```
The cleanup job's retry policy in config.py should allow 5 attempts instead of 3 — keep the other two jobs' limits exactly as they are, and keep the change minimal so it's obvious in a diff what actually moved.
```
All three list entries are identical, so there's no small snippet of text unique to one entry. The reader has to work out that "the cleanup job's policy" is `RETRY_POLICIES[2]` (config.py's docstring maps job → index) before editing it. The actual outcome varies by run:
- A narrow `Edit` fails with `Found 2 matches of the string to replace, but replace_all is false...`. The correct recovery is Read the full file, then Write it back with only that entry changed.
- A wider `Edit` (one that reaches the list's closing `]`) can still succeed in one shot — a capable session doesn't always need the fallback.
- A real session has also solved this with Bash `sed` on a specific line number, sidestepping Edit's uniqueness check entirely.

To see the failure-and-fallback path specifically: "keep the change minimal, and if a single small edit isn't possible because the text isn't unique, read the whole file and rewrite it with just that one change."

```
Trace how the legacy name add_job flows through this codebase — where is it defined, and who actually calls it?
```
Expected: Read `compat.py` first to learn `add_job` is `core.enqueue_task` re-exported, then search for `add_job` itself, landing on its one call site in `cli.py`.

```
Start from cli.py and explain what this program does end to end, tracing its imports as you go.
```
Expected: read `cli.py` first, then follow its imports one at a time (`compat.py` → `core.py` → `workers.py` → `config.py`), without reading `tests/` at all.

---

# Implementation Info
> `core.py`/`compat.py`/`workers.py`/`config.py`/`cli.py` form one small, real, tested task-queue library. `tests/` holds one test file per module. `.claude/settings.json` and `.claude/hooks/log_tool_use.py` log every tool call a live session makes here.

**Tool-call logging** — `.claude/settings.json`, `.claude/hooks/log_tool_use.py`

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
Claude Code runs this after every tool call, passing the tool's name, input, and result as JSON on stdin. It reuses `common/logging_utils.py`'s `append_log`, so the log lands in the same pretty-printed format every other task uses. This hook only fires on *successful* calls — a failed `Edit` never reaches it, which is why the config.py fallback below is logged as `Read` → `Write` with no `Edit` in between.

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

  `enqueue_task` has one definition and four real call sites across three files, plus a docstring example and an import line that look similar but aren't calls. Finding the real calls requires a content search, not a single-file read.

- **Glob for file path pattern matching (finding files by name or extension patterns)** — `tests/`

  ```
  tests/test_cli.py
  tests/test_config.py
  tests/test_core.py
  tests/test_workers.py
  ```

  All four share the `test_*.py` naming convention, distinct from every other file in the folder — a name-pattern match, not a content search. In this environment's headless sessions Glob isn't registered at all, so every run falls back to Bash `find`; the naming-pattern reasoning itself was still correct.

- **Read/Write for full file operations; Edit for targeted modifications using unique text matching** — `core.py`, hook log

  ```python
  """Add a job to the queue. `payload` is any JSON-serializeable dict.
  ```

  This typo appears exactly once, so a single `Edit` call with that line as anchor fixes it — the targeted, unique-text half of this bullet.

  ```json
  {
    "tool_name": "Write",
    "tool_input": { "file_path": ".../task-5-built-in-tool-selection/stats.py", "content": "\"\"\"Observability helpers for the task queue.\"\"\"\n\nfrom core import queue_size\n..." }
  }
  ```

  From the hook's log: asked to add `stats.py` and its test file, the session used `Write` for both, since neither file existed for `Edit` to modify — the full-file-operation half of this bullet.

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

  An `Edit` anchored on just one dict's four lines fails with `Found 2 matches of the string to replace, but replace_all is false...`. The fix is Read the full file, then Write it back with only the intended entry changed. The hook logs this as `Read` → `Write` with no `Edit` in between (`PostToolUse` doesn't fire on failed calls). Real behavior varies: a wider `Edit` can still succeed in one shot, and one real session solved it with Bash `sed` instead — both documented above under "How to verify."

- **Selecting Grep for searching code content across a codebase (e.g., finding all callers of a function, locating error messages)** — hook log

  ```json
  {
    "tool_name": "Bash",
    "tool_input": {
      "command": "grep -rn \"enqueue_task\" .../task-5-built-in-tool-selection --include=\"*.py\""
    }
  }
  ```

  Asked generically, the search runs as Bash `grep`, since Grep is a deferred tool here. Asked explicitly, tool discovery is inconsistent — one run found it via `ToolSearch`, another didn't. The reasoning this bullet is about — excluding the definition, docstring example, and import lines — was correct regardless of which tool ran the search.

- **Selecting Glob for finding files matching naming patterns (e.g., **/*.test.tsx)** — `tests/` directory listing

  This environment's headless sessions don't have Glob registered at all (`ToolSearch` for `select:Glob` returns `No matching deferred tools found`), so every run defaults to Bash `find`. It's tool *availability*, not tool *selection* reasoning, that's limited here — the naming-pattern reasoning was correct every time.

- **Using Read to load full file contents followed by Write when Edit cannot find unique anchor text** — `config.py`, hook log

  A session that hits this scenario logs `Read` then `Write` with no `Edit` call in between — the fix was applied by loading the full file and writing it back, not a second, narrower `Edit` attempt.

- **Building codebase understanding incrementally: starting with Grep to find entry points, then using Read to follow imports and trace flows, rather than reading all files upfront** — `cli.py`

  ```python
  """Command-line entry point for the task-queue demo."""

  from compat import add_job
  from core import enqueue_task
  from workers import process_email_job, process_report_job
  ```

  Asked to trace `cli.py` end to end, the session reads `cli.py`, then `compat.py`, `core.py`, `workers.py`, and `config.py` in that order, following the actual import chain, without opening `tests/`.

- **Tracing function usage across wrapper modules by first identifying all exported names, then searching for each name across the codebase** — `compat.py`

  ```python
  """Legacy aliases for core.py, kept for callers who haven't migrated to the new names yet.

  Do not add new functionality here — this module only re-exports.
  """

  from core import enqueue_task as add_job
  from core import dequeue_task as get_next_job
  ```

  Asked to trace `add_job`, the session reads `compat.py` first to learn it's an alias for `core.enqueue_task`, then searches for `add_job` itself and finds its one call site in `cli.py` — correctly reporting that `get_next_job`, the other alias, has zero callers anywhere.
