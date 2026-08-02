# Context & Reliability Tasks

Scaffolds a task for Context Management & Reliability. Unlike every other domain, this domain's task statements don't share one shape: some (context preservation, escalation criteria, codebase-exploration context management) are pure prompting/session-behavior concerns with nothing to program, while others (human-review confidence calibration, multi-agent error propagation, provenance-preserving synthesis) plausibly need real data or coordination logic. This category is deliberately flexible rather than forcing every task into one artifact shape — the decision below is made fresh per task, not once for the whole domain.

Three rules govern every task built under this category, in this priority order:

1. **Prompts first.** If the task statement's Skills-in bullets can be genuinely demonstrated by a system prompt / subagent instructions / documented prompts fired at a live Claude Code session, do that and nothing else — no script, no `main.py`, no `common/` reuse. This is the default.
2. **Code only when the bullets require it.** Only add a Python script when a bullet genuinely needs computation over data that a single documented session can't show cleanly — e.g. stratified sampling across many labeled records, or measuring accuracy by segment across a dataset. Don't add a script "for thoroughness" if prompting already covers every bullet.
3. **Claude Code, not the Anthropic API, for any programmatic LLM call.** If a script (from rule 2) needs an LLM call — to generate a confidence score, simulate a subagent's structured output, etc. — shell out to headless Claude Code (`claude -p ... --output-format json`) rather than instantiating `anthropic.Anthropic()` or reusing `common/agent_loop.py`. That loop and client belong to Agentic Architecture & Orchestration's Agentic Tool-Use Tasks; this domain demonstrates context/reliability patterns *through* Claude Code itself, not by re-implementing an API loop.

`SKILL.md`'s step 1 (gather inputs) already resolved the task number, domain, and task statement text before handing off to this file — pick up from the shape decision below.

This type exists because Context Management & Reliability was left "not yet built" in `SKILL.md`'s domain table — see that table's note not to default to another domain's shape (e.g. Agentic Tool-Use Tasks) by analogy. Read `wiki/tasks/5-context-management.md`'s actual Task Statement text for the one being built before deciding anything.

## 1. Decide the artifact shape

Before proposing a scenario, decide — and say so explicitly to the user — whether this task needs rule 2's script or stays prompt-only under rule 1:

- Re-read the covered Task Statement's Skills-in bullets. For each one, ask: "can a live Claude Code session, driven by documented prompts and a system prompt / subagent setup, actually exercise this?" If yes for every bullet, this is a **prompt-only task**.
- If at least one bullet requires measuring something across many cases (sampling rates, accuracy by segment, confidence-threshold calibration) or simulating multi-run failure/recovery sequences that a single session transcript can't show, this is a **scripted task**.
- State this decision plainly before scaffolding (e.g. in your own summary to the user) — don't silently pick one path.

## 2. Propose scenario options and confirm with the user before building anything

The **scenario** is the fictional system the task operates in — e.g. a customer-support desk, a multi-source research pipeline, a document-extraction review queue. It must be new every time, same rule as every other type.

- Survey what's already been used: read the `# Subject` section of every existing task README (`head -n 12 tasks/*/*/README.md`). Never repeat a scenario or thinly reskin one.
- Draft 3-4 candidate scenarios that naturally exercise every Knowledge-of/Skills-in bullet for the covered statement, without contrivance. For a prompt-only task, each candidate needs a plausible system prompt / subagent split and a realistic conversation or exploration flow. For a scripted task, each candidate needs a plausible dataset shape (e.g. labeled extractions with confidence scores and document types) that the script can genuinely compute over.
- Present the candidates via `AskUserQuestion` — one option per candidate, each `description` naming the concrete data/conversation shape and which bullets it exercises. Mark a recommended pick, wait for the user's answer before scaffolding anything.
- Carry the chosen scenario through consistently — system prompt, mock data, subagent instructions, and (if scripted) the script's dataset should all read as one coherent scenario.

## 3. Compute the folder path

`tasks/context-management/task-<N>-<kebab-slug>/` — same convention as every other type.

- `<kebab-slug>` = short kebab-case rendering of the task's **type** (e.g. `case-facts-context-preservation`, `stratified-confidence-calibration`) — never the scenario. Scenario only ever appears in the Implemented Tasks table's Topic column and the README's `# Subject` section.

Do not reuse or renumber an existing folder. `ls tasks/context-management/` first if unsure whether `N` is taken (this domain's folder may not exist yet for the first task — create it).

## 4. Scaffold the files

### If prompt-only (rule 1)

Same shape as Session Behavior Tasks — the task folder **is** the sample scenario, not supporting code for a script:

- A handful of small, real, working modules or mock data files forming one coherent scenario (e.g. a mock ticketing/order data module, a set of subagent instruction files) — enough genuine surface area that the documented prompts produce real, checkable behavior.
- A system prompt (and, if the statement calls for subagents — e.g. error propagation or provenance synthesis statements — one instruction file per subagent role) written as plain markdown/text, not Python — there's no agentic loop to wire it into.
- No `common/` reuse, no Anthropic client, no `main.py`/`tools.py`/agentic loop — this shape produces prompting artifacts and mock data, not a runnable program.
- `.claude/settings.json` + `.claude/hooks/log_tool_use.py` — same hook shape as Session Behavior Tasks and Built-in Tool Tasks, logging every tool/subagent call via `common/logging_utils.py`'s `append_log` to `logs/context-reliability/<task-folder-name>.jsonl`. This is what turns a claim like "the coordinator correctly asked for clarification instead of guessing" into a checkable log entry.

### If scripted (rule 2)

- A minimal Python script (e.g. `analyze.py` or `calibrate.py` — name it for what it computes, not `main.py`, since there's no agentic loop) that reads a small mock dataset (`data.py` or a `data/` folder of sample records) and performs the actual computation the bullet requires (stratified sampling, accuracy-by-segment breakdown, confidence-threshold routing).
- If — and only if — the script needs an LLM call (e.g. to generate a confidence score or simulate a subagent's structured finding), it invokes headless Claude Code via `subprocess`, e.g. `claude -p "<prompt>" --output-format json`, and parses the returned JSON. Do not import `anthropic`, do not call `common.client.get_client()`, and do not reuse `common/agent_loop.py` — those belong to Agentic Tool-Use Tasks.
- Still no `common/` reuse beyond generic non-LLM helpers (e.g. `common.bootstrap.find_repo_root()` for path resolution) — this category's whole point is demonstrating the pattern through Claude Code, not through the Agentic Architecture domain's API-loop machinery.

## 5. Write README.md

<readme_template>
  <purpose>
    Same purpose as every other type: prove, with real files pasted in, that every Knowledge-of and Skills-in bullet for the covered task statement is genuinely exercised — plus prove it's actually testable, either via documented prompts against a live Claude Code session (prompt-only) or via a script's real output (scripted). Follow `SKILL.md`'s "README writing style" section for prose — short paragraphs, bullets over run-on sentences, simple language.
  </purpose>

  <section id="1" name="task_statement_header">
    <format>
# Task Statement X.Y: &lt;title, copied verbatim from wiki/tasks/5-context-management.md&gt;
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
&lt;1-2 sentences: what the scenario is and what it's for&gt;
- &lt;bullet, if needed: whether this task is prompt-only or scripted, and why&gt;
    </format>
    <rule>Same plain-language rule as every other type — no file references, no code, written for a reader who hasn't opened anything yet. State the shape decision from step 1 in one line so a reader knows what kind of artifact to expect.</rule>
  </section>

  <separator>---</separator>

  <section id="3" name="how_to_run_or_verify">
    <format_prompt_only>
# How to verify
This task has no script to run — it's prompting artifacts and mock data. Open a Claude Code session with this folder as the working directory, then try the prompts below.

`.claude/settings.json` wires a `PostToolUse` hook that logs every tool/subagent call to `logs/context-reliability/&lt;task-folder-name&gt;.jsonl`. Every claim below is backed by that log.

```
&lt;a prompt exercising one Skills-in bullet&gt;
```
Expected: &lt;specific, checkable observable behavior&gt;

&lt;one prompt per remaining bullet, same shape&gt;
    </format_prompt_only>
    <format_scripted>
# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project; this task also needs the `claude` CLI on `PATH` if it shells out for any LLM step).
```bash
uv run tasks/context-management/task-&lt;N&gt;-&lt;slug&gt;/&lt;script&gt;.py
```
&lt;1-2 sentences describing the real output the reader should see, e.g. the computed sampling rate or accuracy-by-segment table&gt;
    </format_scripted>
    <rule>Pick whichever format matches the shape decision from step 1 — never both. Every prompt (prompt-only) or every run instruction (scripted) must produce something a reader can literally check, not just a plausible-sounding answer.</rule>
  </section>

  <separator>---</separator>

  <section id="4" name="implementation_info">
    <format>
# Implementation Info
&gt; One or two sentences: what the files are and how they fit together.
## How each Task Info item is covered:
- &lt;short label for one Knowledge-of or Skills-in bullet&gt; — `&lt;file&gt;`

  ```python
  &lt;minimal snippet, or the relevant excerpt of a prompt/instruction file&gt;
  ```

  &lt;one sentence on how the snippet, plus the live-verified log or script output, satisfies the bullet&gt;
    </format>
    <rule>Same rule as every other type: every bullet gets exactly one entry, same order, cite by filename only (never a line number), paste the real snippet verbatim.</rule>
  </section>
</readme_template>

## 6. Verify

Actually drive the real artifact rather than describing what it would probably do:

- **Prompt-only:** `cd` into the task folder, run each documented prompt non-interactively (`claude -p "<prompt>" --output-format json`, exporting `ANTHROPIC_API_KEY` from the repo root `.env` first if needed), and check `logs/context-reliability/<task-folder-name>.jsonl` for the actual tool/subagent sequence. Confirm it matches the documented expectation — including cases where the session reasonably diverges; report that honestly rather than only keeping matching runs.
- **Scripted:** run the script with `uv run` and confirm it produces real output over the mock dataset. If it shells out to `claude -p`, confirm that call actually happens (don't stub it) and that the script handles a non-JSON or empty response the same way it would handle any other tool-boundary input — per `CLAUDE.md`'s error-response convention, not a silent fallback.
- Either way, re-open the written README.md and check every pasted snippet still matches the real file verbatim.

## 7. Update CLAUDE.md and README.md once verified

Identical to every other type's table-update step — same table format, same columns, add one row to **both** `CLAUDE.md`'s `### Implemented Tasks` table and the root `README.md`'s `# Tasks` table in the same pass:

| Domain | Task | Topic |
|---|---|---|
| `[Context Management & Reliability](wiki/tasks/5-context-management.md)` | `[Task-<N> - <Small Description>](tasks/context-management/task-<N>-<kebab-slug>/README.md)` | `<topic>` |

- **Task** column's `<Small Description>` is the `<kebab-slug>` from step 3, de-hyphenated into sentence case.
- **Topic** is the scenario's fictional shape, pulled from the task's own README `# Subject` section.

Never add a row to only one of the two files — if you touch one, update the other in the same pass.
