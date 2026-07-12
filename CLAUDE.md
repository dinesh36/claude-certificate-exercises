# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repository contains exercise implementations for the [Claude Certified Architect – Foundations](https://anthropic-partners.skilljar.com/claude-certified-architect-foundations-certification) certification. Each exercise maps to one or more of the five exam domains. The exam guide is at `wiki/exam-guide.pdf` and the exercise list is at `wiki/exercises.md`.

## Exercise Domains

- **Domain 1** – Agentic Architecture & Orchestration (agentic loops, multi-agent coordinator/subagent patterns, session state)
- **Domain 2** – Tool Design & MCP Integration (tool descriptions, error responses, MCP server config)
- **Domain 3** – Claude Code Configuration & Workflows (CLAUDE.md hierarchy, slash commands, skills, CI/CD)
- **Domain 4** – Prompt Engineering & Structured Output (few-shot, JSON schemas via tool_use, batch API)
- **Domain 5** – Context Management & Reliability (context preservation, error propagation, provenance tracking)

## Exercises

| # | Title | Domains |
|---|-------|---------|
| 1 | Multi-Tool Agent with Escalation Logic | 1, 2, 5 |
| 2 | Claude Code Team Development Workflow Config | 2, 3 |
| 3 | Structured Data Extraction Pipeline | 4, 5 |
| 4 | Multi-Agent Research Pipeline | 1, 2, 5 |
| 5 | Coordinator-Subagent Orchestration | 1 |
| 6 | Subagent Invocation & Context Passing | 1 |

## Repository Layout

- `wiki/exam-guide.pdf` — the certification exam guide (source material, do not edit).
- `wiki/exercises/` — one Markdown file per domain (`agentic-architecture.md`, `tool-design-mcp.md`, `claude-code-workflows.md`, `prompt-engineering.md`, `context-management.md`), each broken into numbered `### Task Statement X.Y` sections with `Knowledge of` / `Skills in` bullets, plus `preparation-exercises.md` listing the four exercises end to end. Treat these as reference material — quote from them, don't edit them as part of building an exercise.
- `exercises/` — the practical implementations, one subfolder per domain, one folder per exercise inside that (see naming convention below).
- `common/` — the shared Python package (Anthropic client setup, the generic agentic tool-use loop, structured tool-error helpers) reused across exercises. Installed editable into the root `uv` project, so any exercise script can `from common.x import y` regardless of nesting depth.
- `logs/` — JSON-Lines transcripts written automatically by `common/agent_loop.py`, one file per run.

## Exercise Naming & Folder Convention

Each exercise lives at `exercises/<domain-slug>/task-<N>-<kebab-slug>/`, where:

- `<N>` is the exercise's row number in the Exercises table above (matches `wiki/exercises/preparation-exercises.md` ordering) — global across the repo, not per-domain.
- `<domain-slug>` is the slug of the **first** domain listed for that exercise in the Domains column.
- `<kebab-slug>` is a short kebab-case rendering of the title (e.g. `multi-tool-agent-escalation`).

Domain slugs (fixed — do not invent new ones):

| Domain | Slug |
|---|---|
| 1 – Agentic Architecture & Orchestration | `agentic-architecture` |
| 2 – Tool Design & MCP Integration | `tool-design-mcp` |
| 3 – Claude Code Configuration & Workflows | `claude-code-workflows` |
| 4 – Prompt Engineering & Structured Output | `prompt-engineering` |
| 5 – Context Management & Reliability | `context-management` |

Every exercise folder must contain a `README.md` documenting which task statement(s) it covers and mapping each `Knowledge of`/`Skills in` bullet to the exact file/line range implementing it (see [`exercises/agentic-architecture/task-1-multi-tool-agent-escalation/README.md`](exercises/agentic-architecture/task-1-multi-tool-agent-escalation/README.md) for the canonical example). Code should be split into small per-concern modules (e.g. `main.py` entry point, `tools.py` schemas/implementations, `policy.py` hooks, `data.py` mock data) and reuse `common/` rather than duplicating client setup, the agentic loop, or error-shaping logic. Only add to `common/` when a capability is genuinely reusable across exercises, not exercise-specific logic.

Use the `new-exercise` skill (`.claude/skills/new-exercise/SKILL.md`) to scaffold a new exercise consistent with these conventions.

## Implementation Conventions

When building exercises, use the Anthropic SDK (`@anthropic-ai/sdk` for Node.js or `anthropic` for Python). Default to the latest capable model (`claude-sonnet-4-6` or newer).

Invoke the `/claude-api` skill before writing any Anthropic SDK code — it loads current model IDs, pricing, and API patterns so you don't rely on stale training data.

### Agentic loop pattern (Domain 1)

Terminate loops on `stop_reason === "end_turn"`, continue on `"tool_use"`. Never use arbitrary iteration caps as the primary stopping mechanism or parse assistant text content as a completion indicator.

### Structured output (Domain 4)

Use `tool_use` with a JSON schema for guaranteed schema-compliant output. Set `tool_choice: { type: "tool", name: "..." }` to force a specific extractor; use `tool_choice: "any"` when the document type is unknown. Do not rely on `JSON.parse` of raw assistant text.

### MCP server config (Domain 2)

- Project-shared servers → `.mcp.json` (committed, use `${ENV_VAR}` expansion for credentials)
- Personal/experimental servers → `~/.claude.json` (not committed)

### Error responses from tools (Domain 2)

Return structured metadata: `errorCategory` (`transient` | `validation` | `permission`), `isRetryable` boolean, and a human-readable description. Never return a generic `"Operation failed"` string.
