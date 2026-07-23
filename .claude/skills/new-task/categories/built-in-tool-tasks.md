# Built-in Tool Tasks

Scaffolds a task as a small **sample codebase** that a live Claude Code session navigates using its own built-in tools (Read, Write, Edit, Bash, Grep, Glob) — not an MCP server, and not a script with a `main.py` entry point. Unlike MCP Server Tasks, there's no `server.py`/`FastMCP`/`claude mcp add` anywhere in this category: the sample codebase's own structure (duplicated text, wrapper modules, naming patterns) is what makes one built-in tool the obviously correct choice over another. Verification is a live Claude Code session (or a subagent standing in for one) actually navigating the sample codebase and using the tool the task statement says it should.

`SKILL.md`'s step 1 (gather inputs) already resolved the task number, domain, and task statement text before handing off to this file — pick up from scenario proposal.

This type exists because a Tool Design & MCP Integration task statement can be about Claude Code's *own* built-in tools rather than MCP tool design — see `SKILL.md`'s domain table for how this was discovered (Task Statement 2.5 has no MCP-side expression at all).

## 1. Propose scenario options and confirm with the user before building anything

The **scenario** is the shape of the fictional sample codebase the built-in tools operate against — e.g. a small Python library, a CLI tool, a data pipeline. It must be new every time, same rule as every other type.

- Survey what's already been used: read the `# Subject` section of every existing task README (`head -n 12 tasks/*/*/README.md`). Never repeat a scenario or thinly reskin one.
- Draft 3-4 candidate sample-codebase shapes. Each candidate must naturally contain, without contrivance:
  - A function or symbol with multiple real callers spread across several files (for Grep-finds-callers).
  - Several files sharing a naming pattern (e.g. `test_*.py`) distinct from a content match (for Glob).
  - At least one duplicated, verbatim text block *within a single file* — not just across files — so an `Edit` call targeting it genuinely fails on non-unique anchor text, forcing a documented Read + Write fallback.
  - A wrapper/compat module that re-exports names under an alias, so tracing usage requires reading the wrapper first to learn the alias, then searching for that alias elsewhere.
- Present the candidates via `AskUserQuestion` — one option per candidate, each `description` naming the concrete files/functions and which bullet each one exercises. Mark a recommended pick, wait for the user's answer before scaffolding anything.
- Carry the chosen scenario through consistently — every file, function, and test name should read as one coherent small codebase, not a grab-bag of unrelated snippets.

## 2. Compute the folder path

`tasks/tool-design-mcp/task-<N>-<kebab-slug>/` — same convention as every other type in this domain.

- `<kebab-slug>` = short kebab-case rendering of the task's **type** (e.g. `built-in-tool-selection`) — never the scenario. Scenario only ever appears in the Implemented Tasks table's Topic column and the README's `# Subject` section.

Do not reuse or renumber an existing folder. `ls tasks/tool-design-mcp/` first if unsure whether `N` is taken.

## 3. Scaffold the files

The task folder **is** the sample codebase — everything under it is the graded artifact, not supporting code for a script:

- A handful of small Python (or scenario-appropriate) modules forming one coherent, working mini-library — real enough that Grep/Glob searches return genuine, meaningful results, not staged text. Include a `tests/` folder with a few `test_*.py` files if the task statement mentions file-pattern matching.
- Exactly one duplicated, verbatim multi-line block *inside a single file* (not spread across files) — this is what makes an `Edit` call on that text fail with a non-unique-match error. Don't over-engineer this: a repeated `except`/error-handling block or a repeated constant assignment is enough.
- One wrapper/compat module that re-exports a real function under an alias, so "trace this name through the codebase" requires reading the wrapper first.
- No `common/` reuse, no Anthropic client, no MCP server, no `main.py`/`tools.py`/agentic loop — this category produces a static, working sample codebase, not a runnable agent program.

## 4. Write README.md

<readme_template>
  <purpose>
    Same purpose as every other type's README: prove, with the real sample-codebase files pasted in, that every Knowledge-of and Skills-in bullet for the covered task statement is genuinely exercised — plus prove it's actually testable by documenting exact prompts a reader can fire at a live Claude Code session opened in this folder. Follow `SKILL.md`'s "README writing style" section for prose — short paragraphs, bullets over run-on sentences, simple language.
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
&lt;1-2 sentences: what the sample codebase is and what it's for&gt;
- &lt;bullet, if needed: the specific duplicated-text/wrapper-module mechanic that forces a tool choice&gt;
    </format>
    <rule>Same plain-language rule as every other type — no file references, no code, written for a reader who hasn't opened anything yet.</rule>
  </section>

  <separator>---</separator>

  <section id="3" name="how_to_verify">
    <format>
# How to verify
This task has no script to run — it's a small sample codebase. Open a Claude Code session with this folder as the working directory, then try:

```
&lt;prompt 1 — should route to Grep, not a manual file-by-file read&gt;
```
&lt;expected observable behavior, specific enough to check pass/fail — which tool should fire and what it should find&gt;

```
&lt;prompt 2 — should route to Glob&gt;
```
&lt;expected behavior&gt;

```
&lt;prompt 3 — a one-off, unique-text fix that should route to a clean Edit&gt;
```
&lt;expected behavior&gt;

```
&lt;prompt 4 — targets the duplicated block, should trigger an Edit failure then a documented Read + Write fallback&gt;
```
&lt;expected behavior, including what the failure looks like&gt;

&lt;1-2 more prompts covering any remaining bullets, e.g. tracing a wrapper-module alias or incremental codebase understanding&gt;
    </format>
    <rule>Every prompt must be something a reader can literally paste into a live session and get a checkable answer from. Prefer prompts that would produce a visibly wrong tool choice if the codebase weren't shaped this way, so each prompt actually tests tool selection rather than just touring the code.</rule>
  </section>

  <separator>---</separator>

  <section id="4" name="implementation_info">
    <format>
# Implementation Info
&gt; One or two sentences: what the sample codebase's files are and how they fit together.
## How each Task Info item is covered:
- **&lt;short label for one Knowledge-of or Skills-in bullet&gt;** — `&lt;file&gt;`

  ```python
  &lt;minimal snippet&gt;
  ```

  &lt;one sentence on how the snippet, plus the live-verified tool choice, satisfies the bullet&gt;
    </format>
    <rule>Same rule as every other type: every bullet gets exactly one entry, same order, cite by filename only (never a line number), paste the real snippet verbatim.</rule>
  </section>
</readme_template>

## 5. Verify

There's no `uv run` script here. Instead, actually drive a live session against the sample codebase rather than describing what one would probably do:

1. `cd` into the task folder.
2. For each documented prompt, run it non-interactively: `claude -p "<prompt>" --output-format json`. Parse the returned JSON for `tool_use` content blocks and confirm the *correct* tool (and, for Grep/Glob, a sane pattern) actually fired — not just that the final answer text sounds plausible.
3. For the duplicated-block prompt specifically, confirm the transcript shows an `Edit` call failing (or the agent explicitly reasoning that the anchor text isn't unique) followed by a `Read` and then a `Write` call — the actual fallback sequence, not just a successful edit that got lucky.
4. If `claude -p` is genuinely unavailable in this environment, fall back to the same honesty standard as every other type: state plainly that live verification wasn't possible and why, rather than claiming success.
5. Re-open the written README.md and check every pasted snippet still matches the real file verbatim.

## 6. Update CLAUDE.md and README.md once verified

Identical to every other type's table-update step — same table format, same columns, add one row to **both** `CLAUDE.md`'s `### Implemented Tasks` table and the root `README.md`'s `# Tasks` table in the same pass:

| Domain | Task | Topic |
|---|---|---|
| `[Tool Design & MCP Integration](wiki/tasks/2-tool-design-mcp)` | `[Task-<N> - <Small Description>](tasks/tool-design-mcp/task-<N>-<kebab-slug>/README.md)` | `<topic>` |

- **Task** column's `<Small Description>` is the `<kebab-slug>` from step 2, de-hyphenated into sentence case.
- **Topic** is the sample codebase's fictional shape, pulled from the task's own README `# Subject` section.

Never add a row to only one of the two files — if you touch one, update the other in the same pass.
