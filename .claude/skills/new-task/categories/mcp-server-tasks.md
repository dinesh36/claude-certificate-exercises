# MCP Server Tasks

Scaffolds a task as a **real MCP (Model Context Protocol) server** built with the official Python SDK, registered with Claude Code via `claude mcp add`, and verified by driving it from a live `claude` terminal session with real prompts. There is no Anthropic Messages API call anywhere in this type, no `common/agent_loop.py` reuse, and no `main.py`/`TOOLS` list — Claude Code itself is the MCP client that consumes the server's tools, and Claude Code's own model calls is what does the tool-selection reasoning this category is designed to exercise.

`SKILL.md`'s step 1 (gather inputs) already resolved the task number, domain (2), and task statement text before handing off to this file — pick up from scenario proposal.

## 1. Propose scenario options and confirm with the user before building anything

The **scenario** is the fictional domain the MCP server's tools operate in (e.g. a document/research assistant, an inventory system, a CI/deployment status board). It must be new every time — survey existing scenarios first (`head -n 12 tasks/*/*/README.md` or read the `# Subject` section of every existing task) and never repeat or thinly reskin one.

- Draft 3-4 candidate scenarios for the covered task statement(s). For a tool-*design* statement like 2.1 (clear descriptions and boundaries), each candidate should center on a concrete "before/after" tool-design problem the statement itself calls out — near-identical tool descriptions that cause misrouting, a generic do-everything tool that should be split into purpose-specific ones, etc. — not just a generic set of unrelated tools.
- Present via `AskUserQuestion`, one option per candidate, each `description` naming the concrete tools and the specific design flaw/fix each one demonstrates. Mark a recommended pick, wait for the user's answer before scaffolding anything.
- Carry the chosen scenario through consistently: mock data, tool names, descriptions, and the README's before/after narrative should all read as one coherent scenario.

## 2. Compute the folder path

`tasks/tool-design-mcp/task-<N>-<kebab-slug>/` — same convention as every other task type (see `CLAUDE.md`'s Task Naming & Folder Convention section).

- `<kebab-slug>` = short kebab-case rendering of the task's **type** — the tool-design mechanism demonstrated (e.g. `tool-description-clarity-boundaries`, `structured-error-responses`) — never the fictional scenario. Same rule as every other type: the scenario only ever appears in the Implemented Tasks table's Topic column and the README's `# Subject` section.

Do not reuse or renumber an existing folder. `ls tasks/tool-design-mcp/` first if unsure whether `N` is taken.

## 3. Scaffold the files

- `server.py` — required. Module docstring's first line is `Task <N>: <Title>` (same title-casing rule as every other type). Defines a `SERVER_NAME` constant, creates the FastMCP instance (`mcp = FastMCP(SERVER_NAME)`), and defines every tool directly on it with `@mcp.tool()`. Each tool's **docstring is its description** — the primary signal Claude Code's model uses for tool selection, so it must state: what the tool does, its expected input format (with a concrete example value), what it returns, and — critically for this domain — when to use it **instead of** its nearest sibling tool(s), named explicitly. Type hints on parameters double as the input schema; use precise types (not a bare `str` when the value is really one of a fixed set — use a `Literal`/enum-shaped hint or document the valid set in the docstring). Ends with:
  ```python
  if __name__ == "__main__":
      mcp.run()
  ```
  which runs the server over **stdio** transport (the default) — the transport `claude mcp add` expects for a local Python server.
- Every tool must be wrapped with `common/mcp_logging.py`'s `logged_tool(SERVER_NAME)` decorator, stacked directly under `@mcp.tool()` so it sees the plain function:
  ```python
  @mcp.tool()
  @logged_tool(SERVER_NAME)
  def fetch_user_story(story_id: str) -> dict:
      ...
  ```
  This logs every call's server name, tool name, input parameters, and either its result or the raised error to `logs/mcp/<server-name>-<timestamp>.jsonl` — the same formatted-JSON shape `common/agent_loop.py`'s agentic loop already writes under `logs/`, just for MCP calls instead of Messages API turns. `functools.wraps` inside `logged_tool` preserves the real parameter signature, so FastMCP's schema introspection still sees the original typed parameters, not `(*args, **kwargs)` — verify this isn't broken (`inspect.signature(the_wrapped_tool)` should show the real params) rather than assuming it.
- `data.py` — mock data the tools read from (documents, records, etc.), same convention as every other type.
- Boundary violations (e.g. an unrecognized document id, a non-URL passed to a URL-only tool) should `raise ValueError("...")` with a message that explains the boundary AND names the correct tool to use instead — FastMCP catches the exception and surfaces it to the client as a failed tool call automatically (and `logged_tool` logs the error before re-raising it, so it still reaches the client); no manual error-dict plumbing is needed (that convention is specific to this repo's own `common.errors.tool_error()`, which only applies to the Agentic Tool-Use type's raw Anthropic tool_use loop).
- Add `mcp[cli]` to the root `pyproject.toml`'s `dependencies` the first time this type is used, if it isn't already there.
- No `common/agent_loop.py`, no `common.client`, no `TOOLS` list — none of that applies here. `common/mcp_logging.py` is the one shared module this type does reuse.

## 4. Write README.md

<readme_template>
  <purpose>
    Same purpose as every other type's README: prove, with the real server code pasted in, that every Knowledge-of and Skills-in bullet for the covered task statement is actually implemented — plus prove the server is genuinely usable by documenting the exact terminal commands and prompts a reader needs to register it with Claude Code and exercise it themselves.
  </purpose>

  <section id="1" name="task_statement_header">
    <format>
# Task Statement X.Y: &lt;title, copied verbatim from wiki/tasks/&lt;N&gt;-&lt;domain-slug&gt;.md&gt;
## Knowledge of
- &lt;bullet, copied verbatim&gt;
## Skills in
- &lt;bullet, copied verbatim&gt;
    </format>
    <rule>Identical rule to every other type: copy verbatim, repeat once per statement covered if the task spans more than one.</rule>
  </section>

  <separator>---</separator>

  <section id="2" name="subject_brief">
    <format>
# Subject
&lt;1-2 sentences: what the MCP server's fictional scenario is and what tool-design problem it demonstrates solving&gt;
- &lt;bullet, if needed: the specific before/after contrast being demonstrated&gt;
    </format>
    <rule>Same plain-language rule as every other type — no file references, no code, written for a reader who hasn't opened anything yet.</rule>
  </section>

  <separator>---</separator>

  <section id="3" name="how_to_connect_and_run">
    <format>
# How to connect and run
This task is a real MCP server, not a script you `uv run` directly — Claude Code is the client that talks to it.

1. **Register the server** (run from inside this task folder, so it's scoped to just this task rather than every project on your machine):
   ```bash
   cd tasks/tool-design-mcp/task-&lt;N&gt;-&lt;slug&gt;
   claude mcp add --transport stdio &lt;server-name&gt; -- uv run --directory "$(pwd)" server.py
   ```
   This uses the default **local** scope, stored in `~/.claude.json` keyed to this exact directory — it won't appear in any other project, and won't touch this repo's own root `.mcp.json`. Always include `--directory "$(pwd)"` (evaluated by the shell at registration time, so it bakes in the absolute task-folder path) rather than the bare `uv run server.py` — without it, the stored command is relative and only resolves when Claude Code happens to spawn it with this folder as the process's cwd; from anywhere else `claude mcp list` reports `✘ Failed to connect` even though the registration itself is fine.
2. **Verify it connected:**
   ```bash
   claude mcp list
   ```
   `&lt;server-name&gt;` should show as connected.
3. **Start a Claude Code session from this same directory** and try these prompts — each is designed to exercise one tool-selection decision the task statement is about:
   ```
   &lt;prompt 1 — should route to one specific tool&gt;
   ```
   &lt;what should happen and why, referencing which tool should fire&gt;

   &lt;2-3 more prompts total, each isolating a different tool/boundary&gt;
4. **Leave the server registered.** Once it's built and verified, keep it attached rather than removing it — it should be ready to use without re-registering every time. If you edit `server.py` later, re-attach it (`claude mcp remove &lt;server-name&gt;` then the `claude mcp add` command from step 1 again) so any Claude Code session started after that point spawns the updated code — a session already running when you edit the file keeps its already-spawned process and won't see the change until it reconnects or a new session starts.
    </format>
    <rule>Every prompt must be something a reader can literally paste into a live `claude` session and observe a specific, checkable tool call for — not a rhetorical example. Prefer prompts that would visibly misroute to the wrong tool if the descriptions were vague, so the prompt actually tests the tool-design mechanism instead of just touring the server.</rule>
  </section>

  <separator>---</separator>

  <section id="4" name="implementation_info">
    <format>
# Implementation Info
&gt; One or two sentences: what server.py/data.py contain.
## How each Task Info item is covered:
- **&lt;short label for one Knowledge-of or Skills-in bullet&gt;** — `&lt;file&gt;`

  ```python
  &lt;minimal snippet&gt;
  ```

  &lt;one sentence on how the snippet satisfies the bullet&gt;
    </format>
    <rule>Same rule as every other type: every bullet gets exactly one entry, same order, cite by filename only (never a line number), paste the real snippet verbatim. At least one entry should cite a full tool docstring verbatim (not trimmed) since the docstring-as-description mechanic is the crux of this domain.</rule>
  </section>
</readme_template>

## 5. Verify

Claude Code Configuration & Workflow Tasks' "no way to run a script" caveat does **not** apply here — this environment has the `claude` CLI available, so actually do this rather than just describing it:

1. `uv sync` (or equivalent) so `mcp[cli]` is installed.
2. `cd` into the task folder and run the exact `claude mcp add` command from the README.
3. `claude mcp list` and confirm the server shows connected. `claude mcp get <server-name>` if you need to debug the exact command Claude Code is invoking.
4. Drive it non-interactively for each documented prompt, e.g.:
   ```bash
   claude -p "<prompt>" --allowedTools "mcp__<server-name>__<tool-name>"
   ```
   (`claude mcp list` and the tool's own name tell you the exact `mcp__<server>__<tool>` form.) Confirm the response text or a `--verbose`/transcript check shows the *correct* tool was actually invoked for each prompt — not just that some plausible-sounding text came back.
5. Leave the server attached — do not `claude mcp remove` it once verification passes; the point of registering is that it stays ready to use. If you make further changes to `server.py` after this point (this build or a later one), re-attach it (`claude mcp remove <server-name>` then `claude mcp add` again) so the registration reflects the latest code and any new session spawns the updated server.
6. Re-open the written README.md and check every pasted snippet still matches the real file verbatim.

If step 4 is ever genuinely blocked (e.g. `claude` unavailable in a given environment), fall back to the same honesty standard as every other type: state plainly that live verification wasn't possible and why, rather than claiming success.

## 6. Update CLAUDE.md and README.md once verified

Identical to every other type's table-update step — same table format, same columns, add one row to **both** `CLAUDE.md`'s `### Implemented Tasks` table and the root `README.md`'s `# Tasks` table in the same pass:

| Domain | Task | Topic |
|---|---|---|
| `[Tool Design & MCP Integration](wiki/tasks/2-tool-design-mcp)` | `[Task-<N> - <Small Description>](tasks/tool-design-mcp/task-<N>-<kebab-slug>/README.md)` | `<topic>` |

- **Task** column's `<Small Description>` is the `<kebab-slug>` from step 2 (the tool-design mechanism, never the scenario), de-hyphenated into sentence case.
- **Topic** is the scenario's fictional shape, pulled from the task's own README `# Subject` section.

Never add a row to only one of the two files — if you touch one, update the other in the same pass.
