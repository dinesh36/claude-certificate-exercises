---
name: new-task
description: Scaffold a new Claude Certified Architect prep task under tasks/<domain-slug>/task-<N>-<slug>/, following this repo's established folder naming and README.md format. Use when the user asks to create, add, scaffold, or start a new task in this repository.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# New Task Scaffolder

Scaffolds a new task consistent with the rest of the repo. Every task maps to exactly one domain — domains are never mixed or grouped together, in this skill or in a task's own files. `CLAUDE.md`'s "Task Domains" section is the canonical domain list; this skill refers to domains by name only from here on, not by number — the name alone is unambiguous, so a numeric label would only be a redundant repeat of something already established elsewhere.

Each domain gets its own task **type** (the shape of artifact a task in that domain produces), decided independently per domain. A domain's type is only ever asserted once a task actually built in that domain has confirmed it — never assumed by analogy to another domain, even one that looks similar on paper. Tool Design & MCP Integration is the concrete lesson here: it looked at first like it would share Agentic Architecture & Orchestration's shape, and turned out to need a completely different one (a real MCP server, not an Anthropic-API script) once an actual task statement in that domain was read.

| Domain | Type | Confirmed by |
|---|---|---|
| Agentic Architecture & Orchestration | **Agentic Tool-Use Tasks** — a Python script exercising the Anthropic Messages API tool-use loop (`common/agent_loop.py`), verified by running it with `uv run` | `task-1` through `task-7` under `tasks/agentic-architecture/` |
| Tool Design & MCP Integration | **MCP Server Tasks** — a real MCP server built with the official Python SDK, registered with Claude Code via `claude mcp add`, verified from a live `claude` terminal session. **Exception:** a task statement about Claude Code's own built-in tools (Read/Write/Edit/Bash/Grep/Glob), not MCP tool design, uses **Built-in Tool Tasks** instead — a sample codebase with no MCP server at all, verified the same way but against built-in tools. Don't assume every statement in this domain fits the MCP-server shape; check the statement's actual text first. | `task-1` through `task-4` under `tasks/tool-design-mcp/` (MCP Server Tasks); `task-5` (Built-in Tool Tasks) |
| Claude Code Configuration & Workflows | **Claude Code Configuration & Workflow Tasks** — a sample project demonstrating a Claude Code configuration mechanism, verified via documented prompts in a live Claude Code session. **Exception:** a task statement about a live session's own behavioral judgment (e.g. plan mode vs direct execution, dispatching the `Explore` subagent), not a configuration file, uses **Session Behavior Tasks** instead — a realistic sample codebase with no `CLAUDE.md`/`.claude/rules` hierarchy at all, verified the same way via hook-logged tool calls. Don't assume every statement in this domain fits the configuration-file shape; check the statement's actual text first. | `task-1` through `task-3` under `tasks/claude-code-workflows/` (Claude Code Configuration & Workflow Tasks); `task-4` (Session Behavior Tasks) |
| Prompt Engineering & Structured Output | **Prompt & Extraction Pipeline Tasks** — a Python script that calls the Anthropic Messages/Batch API directly (never `common/agent_loop.py`'s tool-use loop) to demonstrate one prompt-engineering or structured-output technique: explicit-criteria design, few-shot prompting, forced `tool_use` extraction, validation/retry loops, Batch API strategies, or multi-instance/multi-pass review. | `task-1` under `tasks/prompt-engineering/` |
| Context Management & Reliability | **Context & Reliability Tasks** — a flexible shape decided per task: prompts-first (a live Claude Code session + documented prompts, mirroring Session Behavior Tasks, verified via hook-logged tool/subagent calls) unless a task statement's Skills-in bullets genuinely require computation over data, in which case a small script is added — and any programmatic LLM call in that script goes through headless Claude Code (`claude -p`), never the raw Anthropic API/`common/agent_loop.py`. | Not yet confirmed by a built task — category file written ahead of the first task in this domain. |

Each established type's full process (scenario proposal, folder scaffold, file layout, README template, verification, table update) lives in its own file under `categories/` — read the matching one before doing anything else:

- [`categories/agent-loop-tasks.md`](categories/agent-loop-tasks.md) — Agentic Architecture & Orchestration
- [`categories/mcp-server-tasks.md`](categories/mcp-server-tasks.md) — Tool Design & MCP Integration (MCP Server Tasks)
- [`categories/built-in-tool-tasks.md`](categories/built-in-tool-tasks.md) — Tool Design & MCP Integration, built-in-tools exception (Built-in Tool Tasks)
- [`categories/claude-code-config-tasks.md`](categories/claude-code-config-tasks.md) — Claude Code Configuration & Workflows (Claude Code Configuration & Workflow Tasks)
- [`categories/session-behavior-tasks.md`](categories/session-behavior-tasks.md) — Claude Code Configuration & Workflows, session-behavior exception (Session Behavior Tasks)
- [`categories/prompt-extraction-pipeline-tasks.md`](categories/prompt-extraction-pipeline-tasks.md) — Prompt Engineering & Structured Output (Prompt & Extraction Pipeline Tasks)
- [`categories/context-reliability-tasks.md`](categories/context-reliability-tasks.md) — Context Management & Reliability (Context & Reliability Tasks)

Every domain now has an established type. If a future task statement reveals that its established type genuinely doesn't fit (the same way Built-in Tool Tasks and Session Behavior Tasks were split out as exceptions within their domains), propose a fresh type to the user via `AskUserQuestion` and write a new `categories/<name>.md` file for it before scaffolding the task itself — don't silently force the statement into the existing shape.

**Preparation Exercises are the one category with no domain restriction.** Every category above covers exactly one domain's Task Statement; a Preparation Exercise, sourced from `wiki/tasks/6-preparation-exercises.md` instead of a per-domain file, is deliberately written to combine bullets from 2-3 domains at once. If the user is scaffolding a task from that file rather than from a numbered `Task Statement X.Y`, skip straight to [`categories/preparation-exercises.md`](categories/preparation-exercises.md) — it owns its own gather-inputs step and doesn't use the single-domain resolution below.

## 1. Gather inputs (shared across every domain-scoped type)

Not for Preparation Exercises — that category resolves its own inputs in `categories/preparation-exercises.md` step 1. Before writing anything for a domain-scoped type, resolve:

- **Task number (`N`) and title** — `<N>` is the second number of the Task Statement being covered (Task Statement `X.N` → `task-<N>`); numbering restarts at 1 within each domain. Check `tasks/<domain-slug>/` for the highest `task-<N>` already used in that domain and pick the next one. If the user hasn't named a specific Task Statement, ask which one (`X.Y`) the task targets.
- **The single domain covered** — the one domain the targeted Task Statement belongs to. A task never covers more than one domain — if a design genuinely needs concerns from a second domain, that's two tasks, not one; stop and ask the user how to split it rather than tagging one task with both.
- **Task statement text** — read the exact `### Task Statement X.Y: ...` heading plus its `Knowledge of` / `Skills in` bullets from `wiki/tasks/<N>-<domain-slug>.md` (e.g. `wiki/tasks/2-tool-design-mcp.md`). Quote these verbatim later — do not paraphrase.
- **Type** — look up the domain in the table above. Every domain has an established type with a matching category file. If the targeted Task Statement's actual text doesn't fit that domain's established type, treat it as an open design question per the note above rather than forcing it in.

Once the type is known, switch to that type's file under `categories/` and follow it through to the end (scenario confirmation, scaffolding, README, verification, and updating both `CLAUDE.md` and root `README.md`'s Implemented Tasks tables). Do not duplicate those steps here.

## 2. README writing style (shared across every type)

Every category's README template cares about content coverage (every Knowledge-of/Skills-in bullet, cited and evidenced); this section is about how to *write* that content, regardless of type:

- **No long paragraphs.** If a paragraph would run more than 2-3 sentences, break it into short paragraphs or a bulleted list instead. A wall of text hides the one detail a reader actually needs.
- **Keep the language simple.** Prefer short, plain sentences over long ones stitched together with dashes, semicolons, or nested clauses. Say the thing once, directly, instead of qualifying it three times in the same sentence.
- **Bullets over inline lists.** When a sentence is naming 3+ things (steps, examples, verified outcomes), put them in a bulleted list rather than a comma-separated run-on.
- This applies to every prose section of the README (`# Subject`, `# How to run`/`# How to connect and run`/`# How to verify`, and the explanatory sentences under each Implementation Info bullet) — not to the pasted code snippets themselves, which stay verbatim.
