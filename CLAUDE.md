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

Two series exist, each with its own `#` numbering — see the naming convention below for how a `#` maps to a folder name in each case. Exercise 1 is shared between both series (same folder), since it happens to satisfy both the first preparation exercise and Task Statement 1.1.

### Preparation Exercises

The original four end-to-end exercises from `wiki/exercises/preparation-exercises.md`.

| # | Title | Domains | Status |
|---|-------|---------|--------|
| 1 | Multi-Tool Agent with Escalation Logic | 1, 2, 5 | Done |
| 2 | Claude Code Team Development Workflow Config | 2, 3 | Not started |
| 3 | Structured Data Extraction Pipeline | 4, 5 | Not started |
| 4 | Multi-Agent Research Pipeline | 1, 2, 5 | Not started |

### Domain 1 Task-Statement Series

One exercise per Task Statement in `wiki/exercises/agentic-architecture.md`, folder-numbered to match (`task-<N>` covers Task Statement `1.<N>`).

| # | Title | Task Statement | Status |
|---|-------|-----------------|--------|
| 1 | Multi-Tool Agent with Escalation Logic | 1.1 | Done |
| 2 | Coordinator-Subagent Orchestration | 1.2 | Done |
| 3 | Subagent Invocation & Context Passing | 1.3 | Done |
| 4 | IT Access Helpdesk (Multi-Step Enforcement & Handoff) | 1.4 | Done |
| 5 | Multi-Carrier Shipment Tracking (Hooks & Data Normalization) | 1.5 | Done |

## Repository Layout

- `wiki/exam-guide.pdf` — the certification exam guide (source material, do not edit).
- `wiki/exercises/` — one Markdown file per domain (`agentic-architecture.md`, `tool-design-mcp.md`, `claude-code-workflows.md`, `prompt-engineering.md`, `context-management.md`), each broken into numbered `### Task Statement X.Y` sections with `Knowledge of` / `Skills in` bullets, plus `preparation-exercises.md` listing the four exercises end to end. Treat these as reference material — quote from them, don't edit them as part of building an exercise.
- `exercises/` — the practical implementations, one subfolder per domain, one folder per exercise inside that (see naming convention below).
- `common/` — the shared Python package (Anthropic client setup, the generic agentic tool-use loop, structured tool-error helpers) reused across exercises. Installed editable into the root `uv` project, so any exercise script can `from common.x import y` regardless of nesting depth.
- `logs/` — JSON-Lines transcripts written automatically by `common/agent_loop.py`, one file per run.

## Exercise Naming & Folder Convention

Each exercise lives at `exercises/<domain-slug>/task-<N>-<kebab-slug>/`, where `<N>` depends on which series (above) the exercise belongs to:

- **Preparation Exercises**: `<N>` is the exercise's row number in that table.
- **Domain Task-Statement Series** (e.g. the Domain 1 series above): `<N>` is the second number of the Task Statement it covers — Task Statement `X.N` → `task-<N>`. If a second domain later grows its own task-statement series, it gets its own `task-<N>` numbering restarting at 1 within that domain's folder, same as Domain 1's did.
- `<domain-slug>` is the slug of the **first** domain listed for that exercise (Preparation Exercises) or the series' own domain (Task-Statement Series).
- `<kebab-slug>` is a short kebab-case rendering of the title (e.g. `multi-tool-agent-escalation`).

Domain slugs (fixed — do not invent new ones):

| Domain | Slug |
|---|---|
| 1 – Agentic Architecture & Orchestration | `agentic-architecture` |
| 2 – Tool Design & MCP Integration | `tool-design-mcp` |
| 3 – Claude Code Configuration & Workflows | `claude-code-workflows` |
| 4 – Prompt Engineering & Structured Output | `prompt-engineering` |
| 5 – Context Management & Reliability | `context-management` |

Every exercise folder must contain a `README.md` documenting which task statement(s) it covers and mapping each `Knowledge of`/`Skills in` bullet to the file (by name only, never a line number/range — those drift) plus a pasted code snippet demonstrating it (see [`exercises/agentic-architecture/task-1-multi-tool-agent-escalation/README.md`](exercises/agentic-architecture/task-1-multi-tool-agent-escalation/README.md) for the canonical example). Code should be split into small per-concern modules (e.g. `main.py` entry point, `tools.py` schemas/implementations, `policy.py`/`normalize.py` hooks, `data.py` mock data) and reuse `common/` rather than duplicating client setup, the agentic loop, or error-shaping logic. Only add to `common/` when a capability is genuinely reusable across exercises, not exercise-specific logic.

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
