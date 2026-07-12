---
name: new-exercise
description: Scaffold a new Claude Certified Architect prep exercise under exercises/<domain-slug>/task-<N>-<slug>/, following this repo's established folder naming, file layout, common/ reuse, and README.md format. Use when the user asks to create, add, scaffold, or start a new exercise/task in this repository.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# New Exercise Scaffolder

Scaffolds a new exercise so it is indistinguishable in structure from the existing ones — same folder naming, same file split, same `common/` reuse, same README.md shape. The canonical reference implementation is [`exercises/agentic-architecture/task-1-multi-tool-agent-escalation/`](../../../exercises/agentic-architecture/task-1-multi-tool-agent-escalation/). Read its `README.md`, `main.py`, `tools.py`, `policy.py`, and `data.py` before scaffolding a new exercise if you have not already read them in this session.

## 1. Gather inputs

Before writing anything, resolve:

- **Exercise number (`N`)** and **title** — from the Exercises table in `CLAUDE.md` if the user is building one of the four already listed there; otherwise ask the user, or append a new row to that table.
- **Domain(s) covered** — the Domains column for that row. If the user is defining a brand-new exercise, ask which Task Statement(s) (`X.Y`) it targets.
- **Task statement text** — read the exact `### Task Statement X.Y: ...` heading plus its `Knowledge of` / `Skills in` bullets from `wiki/exercises/<domain-slug>.md` for every domain covered. Quote these verbatim later — do not paraphrase.

## 2. Pick a fresh scenario — never reuse a prior exercise's concept

Structure (file split, `common/` reuse, README shape) stays identical across exercises. The **scenario** — the fictional domain the agent/tools operate in, e.g. task-1's electronics-retailer customer-support agent — must be new every time.

- Survey what's already been used: `grep -rl "^Exercise" exercises/*/*/main.py` won't work directly — instead read the module docstring of every existing `exercises/*/*/main.py` (e.g. `head -n 12 exercises/*/*/main.py`) and note each one's scenario/domain (customer support, order refunds, etc.).
- Choose a scenario for the new exercise that is clearly distinct from all of those — a different industry, workflow, and cast of tools/data, not just a renamed copy (e.g. don't ship "customer support for a software subscription" right after "customer support for electronics" — that's the same idea with new nouns). Pick something that still naturally exercises every `Knowledge of`/`Skills in` bullet for the covered task statement(s); the scenario is flavor, the bullets are the requirement.
- If you're short on ideas, draw from varied domains: incident/on-call response, travel booking, healthcare appointment scheduling, DevOps deployment approval, library/inventory management, hiring/recruiting pipeline, legal document review, restaurant reservations, fitness coaching, IoT device fleet management, financial trading compliance, content moderation. Don't reuse one already present in the repo.
- Carry the chosen scenario through consistently: the mock data (`data.py`), tool names/descriptions (`tools.py`), any policy hook (`policy.py`), and the system prompt (`main.py`) should all read as one coherent scenario, not a mashup.

## 3. Compute the folder path

`exercises/<primary-domain-slug>/task-<N>-<kebab-slug>/`

- `<primary-domain-slug>` = slug of the **first** domain listed for this exercise (see domain-slug table in `CLAUDE.md`).
- `<kebab-slug>` = short kebab-case rendering of the title.

Do not reuse or renumber an existing folder. If unsure whether `N` is already taken, `ls exercises/*/` first.

## 4. Scaffold the files

Split code by concern, matching the reference exercise. Not every exercise needs every file — only add a module if the exercise actually has that concern:

- `main.py` — required. Module docstring naming the exercise, its domains, and a 2-3 sentence summary of what it demonstrates. Imports the Anthropic client and loop primitives from `common/` (never re-implement client setup or the tool-use loop locally). Defines the system prompt. `if __name__ == "__main__":` accepts an optional `sys.argv[1]` scenario override with a sensible default, runs the loop, and prints the result.
- `tools.py` — if the exercise defines tools. Tool implementations, then a `TOOLS` schema list, then a `dispatch_tool` function. Use `common.errors.tool_error(...)` for every failure path — never return a bare `"Operation failed"` string.
- `policy.py` — if the exercise needs a programmatic hook (business rule enforced deterministically rather than left to the model/prompt).
- `data.py` — if the exercise needs a mock data store.
- Any other module the exercise genuinely needs — keep the same "one concern per file, short module docstring naming which domain/task statement it demonstrates" pattern.

Reuse from `common/`:
- `common.client.get_client()` / `DEFAULT_MODEL` — Anthropic client + model.
- `common.agent_loop.run_tool_loop` — the agentic loop (terminates on `stop_reason != "tool_use"`; never gate termination on an iteration cap or on parsing assistant text).
- `common.errors.tool_error()` / `is_tool_error()` — structured tool error shape (`errorCategory`, `isRetryable`, `description`).
- `common.bootstrap.find_repo_root()` — path resolution.

If the exercise needs a genuinely new reusable primitive (e.g. multi-agent coordination helpers for a Domain 1.2/1.3 exercise), add it to `common/` rather than inlining it in the exercise folder — but only if it will plausibly be reused by another exercise, not as a place to dump exercise-specific logic.

## 5. Write README.md

<readme_template>
  <purpose>
    The README.md is the graded artifact: it proves, with file/line citations, that every Knowledge-of and Skills-in bullet for the covered task statement(s) is actually implemented. A reviewer should be able to open the README and jump straight to the code satisfying each bullet.
  </purpose>

  <section id="1" name="task_statement_header">
    <format>
# Task Statement X.Y: &lt;title, copied verbatim from wiki/exercises/&lt;domain-slug&gt;.md&gt;
## Knowledge of
- &lt;bullet, copied verbatim&gt;
## Skills in
- &lt;bullet, copied verbatim&gt;
    </format>
    <rule>Copy the heading and every bullet verbatim from the wiki domain file — do not paraphrase. If the exercise spans multiple task statements or domains, repeat this whole block once per statement covered, in domain order.</rule>
  </section>

  <separator>---</separator>

  <section id="2" name="how_to_run">
    <format>
# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run exercises/&lt;domain-slug&gt;/task-&lt;N&gt;-&lt;slug&gt;/main.py
```
    </format>
    <rule>If main.py accepts an optional scenario argument, add 2-3 further `uv run ... "custom message"` examples, each exercising a visibly distinct code path (e.g. happy path, a validation error, a policy-blocked/escalation path) — not just cosmetic variations of the same path.</rule>
  </section>

  <separator>---</separator>

  <section id="3" name="implementation_info">
    <format>
# Implementation Info
&gt; One or two sentences: which file covers which concern.
## How each Task Info item is covered:
- **&lt;short label for one Knowledge-of or Skills-in bullet&gt;:** [`file.py:L-L`](./file.py#LX-LY) — one sentence on what those lines do and how they satisfy the bullet.
    </format>
    <rule>Every bullet from every "Knowledge of" and "Skills in" list quoted in section 1 must have exactly one corresponding line here, in the same order. Cite real file paths and real line ranges (relative links; use `../../../common/...` for shared code) — re-read the file after writing it to confirm the cited lines still match, since edits shift line numbers.</rule>
  </section>
</readme_template>

## 6. Update CLAUDE.md if needed

If this exercise is not yet a row in `CLAUDE.md`'s Exercises table, append it (number, title, domains) using the same table format.

## 7. Verify

Run `uv run exercises/<domain-slug>/task-<N>-<slug>/main.py` from the repo root and confirm it executes end to end (or report exactly why it can't — e.g. missing `ANTHROPIC_API_KEY`). Then re-open the written README.md and check every cited line range still points at the right code.
