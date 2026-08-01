# Preparation Exercises

Scaffolds a task from `wiki/tasks/6-preparation-exercises.md` instead of a single per-domain file. This is the one category with no domain restriction: every other category covers exactly one domain's Task Statement, but a Preparation Exercise is deliberately written to combine Knowledge-of/Skills-in bullets from 2-3 domains at once (see that file's "Domains reinforced" line under each numbered Exercise). Don't split a Preparation Exercise into per-domain pieces to force it into the single-domain rule elsewhere in this skill — combining domains is the point of this category, not a signal to divide the work.

`preparation-exercises/exercise-2-team-development-workflow/`, `exercise-3-structured-data-extraction-pipeline/`, and `exercise-4-multi-agent-research-pipeline/` still exist only as README-only pointer folders — each one documents that its Preparation Exercise's steps are fully covered by existing per-domain tasks elsewhere in the repo, with no code of its own. (`exercise-1-multi-tool-agent-escalation/` started the same way and has since been built out as a real, standalone implementation — see its own `README.md` for what that looks like.) Those remaining pointer folders carry no special status for this category: don't treat them as settled, don't skip past their numbers, and don't model a new build's shape on them. Every Preparation Exercise built through this file produces a genuine, standalone practical implementation — real code and/or real documented prompts, never a README that just links elsewhere. If a target Preparation Exercise number already has a pointer-only folder, build the real implementation into that same folder and overwrite `README.md` in place with the real template (section 5 below) — never delete the file, just replace its contents the same way any other README gets written.

`SKILL.md`'s step 1 (gather inputs) hands off to this file before resolving a single domain, since this category has none. Pick up the whole gather-inputs job here instead.

## 1. Gather inputs

- **Exercise number (`N`) and title** — `N` is the Preparation Exercise's own number in `wiki/tasks/6-preparation-exercises.md` (`### Exercise N: <Title>`), not restarted per domain — there's only one `preparation-exercises/` folder. `ls preparation-exercises/` to see which numbers already have a folder (including the pointer-only ones). If the user hasn't named a specific Preparation Exercise, ask which one.
- **Exercise text** — read the exact `### Exercise N: <Title>` heading, its `**Objective:**` line, every numbered Step, and the `**Domains reinforced:**` line verbatim from `wiki/tasks/6-preparation-exercises.md`. Quote these later — do not paraphrase.
- **Domains reinforced** — read each linked domain's `wiki/tasks/<N>-<domain-slug>.md` file for the specific Task Statement(s) that Preparation Exercise's steps actually draw from, so you know which established type(s) (per `SKILL.md`'s domain table) apply to which step.

## 2. Decide the artifact shape(s), per step

A Preparation Exercise's steps rarely all fit one established type — that's expected, since the whole point is combining domains. Go step by step:

- For each numbered Step, identify which domain/established type it matches (Agentic Tool-Use Tasks, MCP Server Tasks, Built-in Tool Tasks, Claude Code Configuration & Workflow Tasks, Session Behavior Tasks, Prompt & Extraction Pipeline Tasks, or Context & Reliability Tasks) by re-reading that type's category file under `categories/`.
- Default to the smallest number of artifacts that can still exercise every step honestly. Steps that share one runnable program (e.g. an agentic loop step plus a tool-error-handling step) belong in the same script. Steps that fundamentally can't coexist in one artifact (e.g. a live Claude Code session's plan-mode behavior alongside a Python extraction script) get separate files within the same exercise folder, not separate exercise folders.
- Use real code (agentic loop, MCP server, extraction script) wherever a step's Skills-in verb requires actually running something — implementing, testing, measuring. Stay prompt-only (documented prompts against a live Claude Code session, hook-logged) wherever a step is a session-behavior or configuration judgment call that prompting alone can demonstrate. This mirrors Context & Reliability Tasks' rule 1/rule 2 split — apply that same test per step here, not once for the whole exercise.
- State the shape decision plainly before scaffolding: which steps get code, which stay prompt-only, and why.

## 3. Propose scenario options and confirm with the user before building anything

Same process as every other category, with one added constraint: the scenario must let every step — across however many domains this Preparation Exercise reinforces — coexist as one coherent story, not a mashup bolted together step by step.

- Survey what's already used: read the `# Subject` section of every existing task README (`head -n 12 tasks/*/*/README.md`) plus the pointer folders' scenario references. Never repeat one or thinly reskin it.
- Draft 3-4 candidate scenarios that naturally support every step's shape decided in step 2 — e.g. a scenario needs both a plausible tool set for an agentic-loop step and a plausible multi-file layout for a CLAUDE.md/rules step, if the Preparation Exercise calls for both.
- Present via `AskUserQuestion`, one option per candidate, each `description` naming the concrete tool/data/config shape per major step so the user can tell them apart. Mark a recommended pick. Do not scaffold anything until they answer.
- Carry the chosen scenario through every file consistently — mock data, tool names, system prompts, config files should all read as one scenario, not one per step.

## 4. Compute the folder path

`preparation-exercises/exercise-<N>-<kebab-slug>/` — a top-level folder (sibling of `tasks/`, not nested inside it), with no domain slug component, since this category isn't scoped to one domain, and its own `exercise-<N>` prefix rather than the shared `task-<N>` convention used everywhere else in this repo.

- `<kebab-slug>` = short kebab-case rendering of the exercise's **type** (the combination of mechanisms it demonstrates, e.g. `multi-tool-agent-escalation`, `team-development-workflow`) — never the scenario. Same rule as every other category: scenario only ever appears in the tracking table's Topic column and the README's `# Subject` section.
- If `N` already has a pointer-only folder, reuse that same folder and slug rather than creating a second one for the same Preparation Exercise.

## 5. Scaffold the files

Reuse each matching category file's own file-layout guidance for the step(s) it covers — don't invent a new file shape when an established one already fits:

- A step matching **Agentic Tool-Use Tasks** → follow `agent-loop-tasks.md`'s `main.py`/`tools.py`/`policy.py`/`normalize.py`/`data.py` split and `common/` reuse (`common.client`, `common.agent_loop.run_tool_loop`, `common.errors.tool_error`).
- A step matching **MCP Server Tasks** or **Built-in Tool Tasks** → follow `mcp-server-tasks.md` or `built-in-tool-tasks.md` respectively for server/tool layout and attach/logging conventions.
- A step matching **Claude Code Configuration & Workflow Tasks** or **Session Behavior Tasks** → follow `claude-code-config-tasks.md` or `session-behavior-tasks.md` for the config-file/hook-logging layout.
- A step matching **Prompt & Extraction Pipeline Tasks** → follow `prompt-extraction-pipeline-tasks.md` for the direct-Messages/Batch-API script shape.
- A step that's prompt-only (no bullet needs code) → follow `context-reliability-tasks.md`'s rule-1 shape: system prompt / subagent instruction files as plain markdown, `.claude/settings.json` + hook logging to `logs/preparation-exercises/<exercise-folder-name>.jsonl`, no `common/` reuse.
- All of this lives inside the one exercise folder from step 4, organized by concern the same way any multi-concern task would be (e.g. `main.py` + `tools.py` for the coded steps, a `prompts/` or top-level instruction file for the prompt-only steps) — it should still read as one coherent scenario, not a folder of unrelated fragments.

## 6. Write README.md

<readme_template>
  <purpose>
    Same purpose as every other category: prove, with real files pasted in, that every Step for this Preparation Exercise is genuinely exercised. Follow `SKILL.md`'s "README writing style" section for prose.
  </purpose>

  <section id="1" name="exercise_header">
    <format>
# Preparation Exercise N: &lt;Title, copied verbatim from wiki/tasks/6-preparation-exercises.md&gt;
&gt; **Objective:** &lt;copied verbatim&gt;
&gt; **Domains reinforced:** &lt;copied verbatim, keep the original per-domain links&gt;

Source: [`wiki/tasks/6-preparation-exercises.md`](../../wiki/tasks/6-preparation-exercises.md), Exercise N.
    </format>
    <rule>Copy the title, Objective, and Domains-reinforced line verbatim — do not paraphrase.</rule>
  </section>

  <separator>---</separator>

  <section id="2" name="subject_brief">
    <format>
# Subject
&lt;1-2 sentences: what the scenario is and what it does&gt;
- &lt;bullet, if needed: which steps are coded vs. prompt-only, from step 2's shape decision&gt;
    </format>
    <rule>Same plain-language rule as every other category — no file references, no code. State the shape split from step 2 in one line so a reader knows what to expect before opening anything.</rule>
  </section>

  <separator>---</separator>

  <section id="3" name="how_to_run_or_verify">
    <format>
# How to run / verify
See the repository root [README](../../README.md) for one-time setup.

For coded steps:
```bash
uv run preparation-exercises/exercise-&lt;N&gt;-&lt;slug&gt;/&lt;script&gt;.py
```

For prompt-only steps: open a Claude Code session with this folder as the working directory and try the prompts below. `.claude/settings.json` logs every tool/subagent call to `logs/preparation-exercises/&lt;exercise-folder-name&gt;.jsonl`.
```
&lt;a prompt exercising one prompt-only step&gt;
```
Expected: &lt;specific, checkable observable behavior&gt;
    </format>
    <rule>Include only the subsection(s) that apply — omit the prompt-only block entirely if every step is coded, and vice versa. Every run instruction or prompt must produce something a reader can literally check.</rule>
  </section>

  <separator>---</separator>

  <section id="4" name="implementation_info">
    <format>
# Implementation Info
&gt; One or two sentences: what the files are and how they fit together.
## How each Step is covered:
- **Step N — &lt;short label, from the Preparation Exercise's own numbered step text&gt;** — `&lt;file&gt;`

  ```python
  &lt;minimal snippet, or relevant excerpt of a prompt/instruction file&gt;
  ```

  &lt;one sentence: how the snippet satisfies this step, and which domain concept it's reinforcing&gt;
    </format>
    <rule>Keyed by Step number (this exercise's own numbering), not by Knowledge-of/Skills-in bullet — Preparation Exercises are written as Steps, unlike domain files' bullets. Every Step gets exactly one entry, same order, cite by filename only (never a line number), paste the real snippet verbatim.</rule>
  </section>
</readme_template>

## 7. Verify

Match the verification method to each step's shape from step 2, same as any mixed-shape task:

- **Coded steps:** run with `uv run` (or the real MCP-server attach-and-call flow, if that shape applies) and confirm real output end to end. If a live run isn't possible, fall back to direct static validation and report that honestly.
- **Prompt-only steps:** run the documented prompts against a live Claude Code session (`claude -p "<prompt>" --output-format json`) and check `logs/preparation-exercises/<exercise-folder-name>.jsonl` for the actual tool/subagent sequence, confirming it matches the documented expectation.
- Either way, re-open the written README.md and check every pasted snippet still matches the real file verbatim.

## 8. Update CLAUDE.md and README.md once verified

Preparation Exercises get their own table, separate from the per-domain "Implemented Tasks" table, since a single Domain-column cell can't represent a task that spans several domains. Add one row to **both** `CLAUDE.md`'s `### Implemented Preparation Exercises` table and the root `README.md`'s matching table — same three columns, same row, in both places:

| Task | Domains Reinforced | Topic |
|---|---|---|
| `[Exercise-<N> - <Small Description>](preparation-exercises/exercise-<N>-<kebab-slug>/README.md)` | `[Domain X](wiki/tasks/<N>-<domain-slug>), [Domain Y](wiki/tasks/<N>-<domain-slug>), ...` | `<topic>` |

- **Task** — `Exercise-<N> - <Small Description>` as the link text, linked to the exercise's own `README.md`. `<Small Description>` is the `<kebab-slug>` from step 4, de-hyphenated into sentence case — must match the Preparation Exercise's title used in the README.
- **Domains Reinforced** — every domain link from the source `**Domains reinforced:**` line, comma-separated, same link style as the per-domain table.
- **Topic** — one line, 10 words max, naming the fictional scenario, pulled from the exercise's own README `# Subject` section.

Never add a row to only one of the two files — if you touch one, update the other in the same pass.
