# Session Behavior Tasks

Scaffolds a task as a **realistic sample codebase** paired with a set of documented prompts spanning a deliberate complexity gradient — genuinely simple, genuinely architectural, and genuinely discovery-heavy. Unlike Claude Code Configuration & Workflow Tasks, there's no `CLAUDE.md`/`.claude/rules` hierarchy to build here: the graded behavior is a live Claude Code session's own judgment about which session-level mechanism fits a given request (plan mode vs direct execution, dispatching the `Explore` subagent vs reading everything inline), not a config file. Verification is the same hook-based logging Built-in Tool Tasks uses — a `PostToolUse` hook captures whether `EnterPlanMode`/`ExitPlanMode` or an `Agent` call with `subagent_type: Explore` actually fired.

`SKILL.md`'s step 1 (gather inputs) already resolved the task number, domain, and task statement text before handing off to this file — pick up from scenario proposal.

This type exists because a Claude Code Configuration & Workflows task statement can be about a live session's own behavioral judgment rather than a configuration mechanism — see `SKILL.md`'s domain table for how this was discovered (Task Statement 3.4 has no `CLAUDE.md`/`.claude/` artifact to build at all).

## 1. Propose scenario options and confirm with the user before building anything

The **scenario** is the fictional codebase the sample prompts operate against — e.g. an e-commerce checkout service, a data-pipeline ETL system, a reporting engine. It must be new every time, same rule as every other type.

- Survey what's already been used: read the `# Subject` section of every existing task README (`head -n 12 tasks/*/*/README.md`). Never repeat a scenario or thinly reskin one.
- Draft 3-4 candidate codebases. Each candidate must naturally support, without contrivance:
  - A genuinely simple, well-scoped request (a single validation check, a one-function fix) — direct execution is obviously correct here.
  - A genuinely complex, architectural request (a multi-file migration, a new cross-cutting pattern) — plan mode is obviously correct here.
  - A genuinely verbose discovery request (find every reference to something across the codebase before removing/changing it) — the `Explore` subagent is obviously correct here, to keep the verbose search output out of the main conversation.
- Present the candidates via `AskUserQuestion` — one option per candidate, each `description` naming the concrete simple/complex/discovery asks it supports. Mark a recommended pick, wait for the user's answer before scaffolding anything.
- Carry the chosen scenario through consistently — every file and function should read as one coherent small-to-mid-size codebase, not a grab-bag of unrelated snippets.

## 2. Compute the folder path

`tasks/claude-code-workflows/task-<N>-<kebab-slug>/` — same convention as every other type.

- `<kebab-slug>` = short kebab-case rendering of the task's **type** (e.g. `plan-mode-vs-direct-execution`) — never the scenario. Scenario only ever appears in the Implemented Tasks table's Topic column and the README's `# Subject` section.

Do not reuse or renumber an existing folder. `ls tasks/claude-code-workflows/` first if unsure whether `N` is taken.

## 3. Scaffold the files

The task folder **is** the sample codebase — everything under it is the graded artifact, not supporting code for a script:

- A handful of small, real, working modules forming one coherent codebase — enough genuine surface area that "this touches 15+ files and several architectural decisions" reads as true, not staged. A `tests/` folder if the scenario calls for it.
- At least one deliberately deprecated/legacy piece (a class, function, or module) referenced from a couple of call sites — this is what makes the discovery ask ("find every reference before removing it") a real multi-file search, not a single-file lookup.
- No `common/` reuse, no Anthropic client, no MCP server, no `main.py`/`tools.py`/agentic loop, no nested `CLAUDE.md` hierarchy — this category produces a static sample codebase whose own complexity is the point, not its configuration.
- `.claude/settings.json` + `.claude/hooks/log_tool_use.py` — same hook shape as Built-in Tool Tasks (see `tasks/tool-design-mcp/task-5-built-in-tool-selection/.claude/`), logging every tool call via `common/logging_utils.py`'s `append_log` to `logs/session-behavior/<task-folder-name>.jsonl`. This is what turns "the session correctly entered plan mode" from a claim into a checkable log entry.

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
- &lt;bullet, if needed: which asks map to simple/complex/discovery, and why each one genuinely is that&gt;
    </format>
    <rule>Same plain-language rule as every other type — no file references, no code, written for a reader who hasn't opened anything yet.</rule>
  </section>

  <separator>---</separator>

  <section id="3" name="how_to_verify">
    <format>
# How to verify
This task has no script to run — it's a small sample codebase. Open a Claude Code session with this folder as the working directory, then try the prompts below.

`.claude/settings.json` wires a `PostToolUse` hook that logs every tool call to `logs/session-behavior/&lt;task-folder-name&gt;.jsonl`. Every claim below is backed by that log.

```
&lt;a genuinely simple, well-scoped request&gt;
```
Expected: direct execution, no `EnterPlanMode` call.

```
&lt;a genuinely complex, architectural request&gt;
```
Expected: an `EnterPlanMode` call before any code changes.

```
&lt;a genuinely verbose discovery request&gt;
```
Expected: an `Agent` call with `subagent_type: Explore`, not an inline Grep/Read sweep of every file.

&lt;1-2 more prompts covering any remaining bullets, e.g. combining plan mode for investigation with direct execution for implementation&gt;
    </format>
    <rule>Every prompt must be something a reader can literally paste into a live session and get a checkable answer from. Report real outcomes honestly, including any run where the session's behavior varied or didn't match the expected mechanism — this category inherits the same honesty standard as every other type.</rule>
  </section>

  <separator>---</separator>

  <section id="4" name="implementation_info">
    <format>
# Implementation Info
&gt; One or two sentences: what the sample codebase's files are and how they fit together.
## How each Task Info item is covered:
- &lt;short label for one Knowledge-of or Skills-in bullet&gt; — `&lt;file&gt;`

  ```python
  &lt;minimal snippet&gt;
  ```

  &lt;one sentence on how the snippet, plus the live-verified tool-call log, satisfies the bullet&gt;
    </format>
    <rule>Same rule as every other type: every bullet gets exactly one entry, same order, cite by filename only (never a line number), paste the real snippet verbatim.</rule>
  </section>
</readme_template>

## 5. Verify

Actually drive a live session against the sample codebase rather than describing what one would probably do:

1. `cd` into the task folder.
2. For each documented prompt, run it via a hooked `claude -p` session (export `ANTHROPIC_API_KEY` from the repo root `.env` first if the CLI reports an expired OAuth session).
3. Check `logs/session-behavior/<task-folder-name>.jsonl` for the actual tool sequence — confirm `EnterPlanMode` fired (or didn't) as expected, and confirm `Agent` calls used `subagent_type: Explore` for the discovery prompt.
4. If real behavior varies between runs, or a session picks a different but still-reasonable path, document that honestly rather than only keeping the run that matched the tidy expectation.
5. Re-open the written README.md and check every pasted snippet still matches the real file verbatim.

## 6. Update CLAUDE.md and README.md once verified

Identical to every other type's table-update step — same table format, same columns, add one row to **both** `CLAUDE.md`'s `### Implemented Tasks` table and the root `README.md`'s `# Tasks` table in the same pass:

| Domain | Task | Topic |
|---|---|---|
| `[Claude Code Configuration & Workflows](wiki/tasks/3-claude-code-workflows)` | `[Task-<N> - <Small Description>](tasks/claude-code-workflows/task-<N>-<kebab-slug>/README.md)` | `<topic>` |

- **Task** column's `<Small Description>` is the `<kebab-slug>` from step 2, de-hyphenated into sentence case.
- **Topic** is the sample codebase's fictional shape, pulled from the task's own README `# Subject` section.

Never add a row to only one of the two files — if you touch one, update the other in the same pass.
