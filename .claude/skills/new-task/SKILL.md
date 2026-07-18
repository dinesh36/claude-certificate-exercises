---
name: new-task
description: Scaffold a new Claude Certified Architect prep task under tasks/<domain-slug>/task-<N>-<slug>/, following this repo's established folder naming and README.md format. Use when the user asks to create, add, scaffold, or start a new task in this repository.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# New Task Scaffolder

Scaffolds a new task consistent with the rest of the repo. Tasks fall into two genuinely different **categories** depending on which domain they cover, and the two categories produce a different *shape* of artifact — do not assume every task looks like a Python script hitting the Anthropic API.

- **Category A — agentic tool-use tasks** (Domains 1, 2, 4, 5): a Python script that exercises the Anthropic Messages API tool-use loop (`common/agent_loop.py`), verified by literally running it with `uv run`. This is every task built so far (`task-1` through `task-5` under `tasks/agentic-architecture/`).
- **Category B — Claude Code configuration & workflow tasks** (Domain 3 only): a small sample project (its own nested `CLAUDE.md` hierarchy, `.claude/` config, etc.) that demonstrates a Claude Code configuration mechanism. There is no Anthropic API call anywhere in this category — it's verified by a human opening a live Claude Code session inside the sample project and trying documented sample prompts, not by running a script.

Each category's full process (scenario proposal, folder scaffold, file layout, README template, verification, table update) lives in its own file under `categories/` — read the matching one before doing anything else:

- [`categories/agent-loop-tasks.md`](categories/agent-loop-tasks.md) — Category A
- [`categories/claude-code-config-tasks.md`](categories/claude-code-config-tasks.md) — Category B

## 1. Gather inputs (shared across both categories)

Before writing anything, resolve:

- **Task number (`N`) and title** — `<N>` is the second number of the Task Statement being covered (Task Statement `X.N` → `task-<N>`); numbering restarts at 1 within each domain. Check `tasks/<domain-slug>/` for the highest `task-<N>` already used in that domain and pick the next one. If the user hasn't named a specific Task Statement, ask which one(s) (`X.Y`) the task targets.
- **Domain(s) covered** — the domain(s) the targeted Task Statement(s) belong to.
- **Task statement text** — read the exact `### Task Statement X.Y: ...` heading plus its `Knowledge of` / `Skills in` bullets from `wiki/tasks/<N>-<domain-slug>.md` (e.g. `wiki/tasks/3-claude-code-workflows.md` for Domain 3) for every domain covered. Quote these verbatim later — do not paraphrase.
- **Category** — Domain 3 → Category B; Domains 1, 2, 4, or 5 → Category A. If a single task would have to span a Category A domain and a Category B domain at once, stop and ask the user how to split it into separate tasks rather than blending the two artifact shapes together.

Once the category is known, switch to that category's file under `categories/` and follow it through to the end (scenario confirmation, scaffolding, README, verification, and updating both `CLAUDE.md` and root `README.md`'s Implemented Tasks tables). Do not duplicate those steps here.
