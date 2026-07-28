# Prompt & Extraction Pipeline Tasks

Scaffolds a task as **a real sample file + a README of copy-pasteable prompts**, verified by the user themselves in a live Claude Code session — not a Python script the builder runs. The default artifact is the sample document/code itself, written as its own naturally-named file (e.g. `intake_validator.py`, `invoice_2024_03.txt`) rather than a string embedded in a `.py` module, plus a `README.md` whose "How to verify" section gives prompts that tell Claude Code to *read that file by path* rather than pasting its content inline. There is no `main.py`, no client, no agentic loop, and no automated scoring shipped in the task folder.

This means verification depends on file-read access, so it requires a live **Claude Code** session, not claude.ai's chat (which can't resolve a local repo path on its own). Say this explicitly in every README's "How to verify" section — don't imply the prompts work pasted into claude.ai as-is.

**Escape hatch:** write a runnable Python script (`main.py` + supporting modules) only when the technique cannot be demonstrated through a plain conversational prompt — i.e. it depends on an API-level parameter with no chat-UI equivalent (forced `tool_choice`, the Message Batches API). Check step 0 before assuming a statement needs this; most don't. When the escape hatch does apply, fall back to this file's prior script-based shape: `main.py` calling `common.client.get_client()`/`DEFAULT_MODEL` or `common.subagent.run_subagent` directly (never `common/agent_loop.py`'s tool-use loop, which is Agentic Architecture & Orchestration's shape, not this domain's), verified with `uv run` the same way other categories verify scripts.

This type exists because Prompt Engineering & Structured Output's task statements are about the *wording and structure of a prompt*, not a program — a person can fully exercise "does explicit criteria beat vague instructions" or "does few-shot improve consistency" by pointing Claude Code at a real sample file and reading the replies. Building a script to do that for them adds a maintenance burden (a `main.py` per task, an ad hoc scorer, a live API call on every verification) without adding evidence a human reader can't get faster by trying it themselves. Using a real file instead of an inlined string additionally means the prompt itself demonstrates the review target the way an actual reviewer would receive it — a file in a repo, not a code block pasted into a chat.

`SKILL.md`'s step 1 (gather inputs) already resolved the task number, domain, and task statement text before handing off to this file — pick up from scenario proposal.

## 0. Which task statement needs the escape hatch

Read the actual statement text (never assume from the number alone). Default to the manual-prompt shape unless the row says otherwise:

| Statement | Core mechanic | Shape |
|---|---|---|
| 4.1 — explicit criteria vs vague instructions | Paste the same input under two system-style prompts (vague vs criteria-based) and compare precision by eye | Manual prompt |
| 4.2 — few-shot prompting | Paste the same extraction/judgment with and without few-shot examples; compare consistency by eye | Manual prompt |
| 4.3 — structured output via `tool_use` + JSON schema | `tool_choice` (`auto`/`any`/forced-named-tool) is an API request parameter — there is no chat-UI equivalent a user can type | **Escape hatch** — needs `main.py` calling `client.messages.create(tools=..., tool_choice=...)` directly |
| 4.4 — validation, retry, feedback loops | Multi-turn: get an extraction, spot the specific inconsistency, paste it back as a correction request — all doable as ordinary chat turns | Manual prompt (multi-turn) |
| 4.5 — batch processing strategies | The Message Batches API (submission, polling, `custom_id` correlation) has no chat-UI equivalent at all | **Escape hatch** — needs `main.py`/`batch.py` calling `client.messages.batches.*` |
| 4.6 — multi-instance / multi-pass review | Open two independent chats/sessions with the same generated code and no shared history; compare their findings | Manual prompt (parallel sessions) |

## 1. Propose scenario options and confirm with the user before building anything

The **scenario** is the fictional document type / review target the prompts operate on (e.g. an invoice-extraction pipeline, a code-review bot, a contract-clause extractor) — it must be new every time, same rule as every other type.

- Survey what's already been used: read the `# Subject` section of every existing task README (`head -n 12 tasks/*/*/README.md`). Never repeat a scenario or thinly reskin one.
- Draft 3-4 candidate scenarios that naturally exercise the target statement(s)' bullets without contrivance. For extraction-heavy statements, each candidate needs source material varied enough in structure to make the technique genuinely necessary (e.g. inconsistent formatting, sometimes-missing fields, plausible-looking false positives) — not clean, uniform inputs a single obvious prompt would already handle perfectly.
- Present the candidates via `AskUserQuestion` — one option per candidate, each `description` naming the concrete document/input type and which bullets it exercises. Mark a recommended pick, wait for the user's answer before scaffolding anything.
- Carry the chosen scenario through consistently: the resource file's sample content, the prompts in the README, and (for escape-hatch statements) the script's system prompt and schema should all read as one coherent scenario.

## 2. Compute the folder path

`tasks/prompt-engineering/task-<N>-<kebab-slug>/`

- `<kebab-slug>` = short kebab-case rendering of the task's **type** (the technique it demonstrates, e.g. `explicit-criteria-precision`, `few-shot-consistency`, `structured-output-tool-schemas`) — never the scenario. The scenario belongs only in the Implemented Tasks table's Topic column and the README's `# Subject` section.

Do not reuse or renumber an existing folder. `ls tasks/prompt-engineering/` first if unsure whether `N` is taken.

## 3. Scaffold the files

**Default shape (manual-prompt statements — 4.1, 4.2, 4.4, 4.6 and any statement not flagged in step 0):**

- `<natural-filename>` — the sample document/code itself, as its own real file with whatever extension/name it would actually have (e.g. `intake_validator.py`, `invoice_2024_03.txt`, `contract_v2.md`). This is what the README's prompts point Claude Code at with a relative path — never inline this content into a prompt or a `.py` string constant. It must be syntactically/structurally valid for its type (a `.py` sample should actually parse) even though nothing imports or runs it.
- `README.md` — the graded artifact (see step 4). Its "How to verify" section contains full prompts that tell Claude Code to read the sample file by path, run per-prompt, plus a Checklist of ground-truth findings/extractions written directly in prose.
- **No separate ground-truth data file.** Do not add a `data.py` (or similar) to hold expected findings/extractions — nothing ever imports it (no script reads it, and the prompts only ever reference the sample file above), so it either sits unused or duplicates the README Checklist's prose verbatim, which is a second source of truth that can drift from the first. Write the ground truth once, directly in the README's Checklist section.
- Nothing else. No `main.py`, `tools.py`, `policy.py`, or `common/` imports in the task folder.

**Escape-hatch shape (4.3, 4.5, or any statement step 0 flags as needing an API parameter with no chat equivalent):** follow the prior script-based shape — `main.py` (required, builds its own client via `common.client.get_client()`/`DEFAULT_MODEL`, never imports `run_tool_loop`), plus `tools.py` (raw Anthropic tool-schema dicts only, for 4.3 — no `implementation` callables, since `main.py` reads `tool_use.input` directly), `batch.py` (for 4.5 — build/submit/poll/retrieve/resubmit-by-`custom_id`), `validation.py` if a retry loop needs semantic error strings, and `data.py` for sample inputs. Reuse `common.client`, `common.subagent.run_subagent` (text-only isolated calls), and `common.logging_utils.append_log` (useful for a retry transcript) as needed. Verified with `uv run tasks/prompt-engineering/task-<N>-<slug>/main.py`, same standard as every script-based category.

## 4. Write README.md

<readme_template>
  <purpose>
    Same purpose as every other type's README: prove, with the real prompts and sample content pasted in, that every Knowledge-of and Skills-in bullet for the covered task statement(s) is genuinely exercised — and prove it's actually testable by giving a reader exact prompts to paste and exact things to look for in the response. Follow `SKILL.md`'s "README writing style" section for prose — short paragraphs, bullets over run-on sentences, simple language.
  </purpose>

  <section id="1" name="task_statement_header">
    <format>
# Task Statement 4.Y: &lt;title, copied verbatim from wiki/tasks/4-prompt-engineering.md&gt;
## Knowledge of
- &lt;bullet, copied verbatim&gt;
## Skills in
- &lt;bullet, copied verbatim&gt;
    </format>
    <rule>Copy the heading and every bullet verbatim — do not paraphrase. Repeat this whole block once per statement covered, in statement order, if the task spans more than one.</rule>
  </section>

  <separator>---</separator>

  <section id="2" name="subject_brief">
    <format>
# Subject
&lt;1-2 sentences: what the fictional document/review scenario is and what technique the prompts demonstrate&gt;
- &lt;bullet, if needed: a specific mechanic worth calling out, e.g. the deliberately inconsistent source formatting, the retry trigger, the false-positive lure&gt;
    </format>
    <rule>Plain-language orientation for a reader who hasn't opened any code yet — no file references, no code, no task-statement jargon.</rule>
  </section>

  <separator>---</separator>

  <section id="3" name="how_to_verify">
    <format>
# How to verify
This task has no script to run. Open a **Claude Code** session at the repository root (the prompts below ask it to read a file by path, so it needs file access — this won't work pasted into claude.ai's chat, which can't resolve a local path).

### 1. &lt;short label, e.g. "Vague prompt"&gt;
```
&lt;full copy-pasteable prompt text, referencing the sample file by its relative path, e.g. "Read tasks/prompt-engineering/task-&lt;N&gt;-&lt;slug&gt;/&lt;filename&gt; and ..."&gt;
```
&lt;what to look for in the response — specific enough to check pass/fail, e.g. "should catch the SQL injection but may also flag the intentional RETRY_ naming convention"&gt;

### 2. &lt;short label, e.g. "Explicit-criteria prompt"&gt;
```
&lt;full copy-pasteable prompt text&gt;
```
&lt;what to look for, and what should differ from step 1&gt;

&lt;repeat for every prompt variant the task compares — typically 2-4&gt;

### Checklist
&lt;a short table or bullet list of the ground-truth findings/extractions, written directly here in prose, so the reader can tick each one off against what they actually saw, instead of trusting a scorer they can't see run&gt;
    </format>
    <rule>Every prompt must be copy-paste-ready exactly as written, referencing the sample file by its relative path rather than inlining its content — no placeholders the reader has to fill in beyond that path. If a technique needs multiple turns (e.g. 4.4's retry loop, 4.6's independent-instance comparison), number the turns/sessions explicitly and say whether they belong in the same conversation or separate ones (4.6 specifically requires separate sessions with no shared history — say so). The referenced path must point at a real file that actually exists in the task folder with that exact content — never a path that doesn't resolve.</rule>
  </section>

  <separator>---</separator>

  <section id="4" name="implementation_info">
    <format>
# Implementation Info
&gt; One or two sentences: what the sample file contains and how the README's prompts reference it.
## How each Task Info item is covered:
- &lt;short label for one Knowledge-of or Skills-in bullet&gt; — `&lt;sample file or README.md; data.py only exists at all for escape-hatch tasks&gt;`

  ```
  &lt;minimal snippet, or the relevant prompt excerpt if the bullet is covered by prompt wording rather than file content&gt;
  ```

  &lt;one sentence on how the snippet satisfies the bullet&gt;
    </format>
    <rule>Every bullet from every "Knowledge of" and "Skills in" list quoted in section 1 must have exactly one corresponding entry here, in the same order. A bullet can cite `README.md` itself (e.g. quoting a prompt's exact wording) when the bullet is about prompt design rather than sample content — that's expected for this category, unlike script-based ones where everything lives in `.py` files. Cite by filename only, never a line number. Paste real content verbatim, trimmed to just what demonstrates the bullet.</rule>
  </section>
</readme_template>

## 5. Verify

There is no committed script to run, and the task is not "done" until a human confirms it — but the builder still owes a sanity check before handing it off, so the README's claims aren't guesses:

1. Confirm the sample file actually exists at the exact relative path every prompt references — a broken path fails silently different ways in different sessions, so check it directly (`ls`/`Read`) rather than assuming.
2. Sanity-check every prompt in the README actually produces the claimed contrast. Dispatch an `Agent` (or equivalent subagent with Read access) with each documented prompt verbatim and let it read the real file, the same way the eventual user's Claude Code session will — this exercises the actual mechanism (file read, not pasted text), unlike a raw `client.messages.create` call. Never leave scratch scripts in the task folder afterward, and never commit a `main.py` for this default shape.
3. If a live check isn't possible (no API key, no credits, no agent dispatch available), say so plainly instead of asserting the prompts work — the same honesty standard as every other category.
4. Re-open the written README.md and confirm every prompt's referenced path is correct, and that the "what to look for" text under each prompt matches what the sanity-check runs actually returned (or is a reasonable, hedged expectation if outputs are known to vary — note the non-determinism explicitly rather than overclaiming a guaranteed result).
5. Tell the user the task is scaffolded and sanity-checked, and that final verification — actually trying the prompts themselves in their own Claude Code session — is theirs to do.

For escape-hatch tasks (4.3, 4.5), verify the same way Agentic Tool-Use Tasks does: run `uv run tasks/prompt-engineering/task-<N>-<slug>/main.py` from the repo root and confirm it executes end to end, or report exactly why it can't.

## 6. Update CLAUDE.md and README.md once verified

Only after step 5 actually passes. Add one row to **both** `CLAUDE.md`'s `### Implemented Tasks` table and the root `README.md`'s `# Tasks` table — same three columns, same row, in both places:

| Domain | Task | Topic |
|---|---|---|
| `[Prompt Engineering & Structured Output](wiki/tasks/4-prompt-engineering)` | `[Task-<N> - <Small Description>](tasks/prompt-engineering/task-<N>-<kebab-slug>/README.md)` | `<topic>` |

- **Task** column's `<Small Description>` is the `<kebab-slug>` from step 2, de-hyphenated into sentence case (e.g. `validation-retry-feedback-loops` → `Validation retry feedback loops`).
- **Topic** — one line, 10 words max, naming the fictional document/review scenario, pulled from the task's own README `# Subject` section.

Never add a row to only one of the two files — if you touch one, update the other in the same pass.
