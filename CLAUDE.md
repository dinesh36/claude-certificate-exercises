# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repository contains task implementations for the [Claude Certified Architect – Foundations](https://anthropic-partners.skilljar.com/claude-certified-architect-foundations-certification) certification. Each task maps to exactly one of the five exam domains — domains are never mixed within a single task, even incidentally in a module docstring or description. If a task's design genuinely touches concerns from a second domain, that's a signal to split it into two separate tasks, not to label one task with both domains. The exam guide is at `wiki/exam-guide.pdf` and the task list is at `wiki/tasks/README.md`.

## Task Domains

- **Domain 1** – Agentic Architecture & Orchestration (agentic loops, multi-agent coordinator/subagent patterns, session state)
- **Domain 2** – Tool Design & MCP Integration (tool descriptions, error responses, MCP server config)
- **Domain 3** – Claude Code Configuration & Workflows (CLAUDE.md hierarchy, slash commands, skills, CI/CD)
- **Domain 4** – Prompt Engineering & Structured Output (few-shot, JSON schemas via tool_use, batch API)
- **Domain 5** – Context Management & Reliability (context preservation, error propagation, provenance tracking)

## Tasks

### Implemented Tasks

One row per completed task, added only once it's actually built and verified — see the `new-task` skill for how a task gets added here.

| Domain | Task | Topic |
|---|---|---|
| [Agentic Architecture & Orchestration](wiki/tasks/1-agentic-architecture) | [Task-1 - Multi tool agent escalation](tasks/agentic-architecture/task-1-multi-tool-agent-escalation/README.md) | A customer-support agent for an online electronics retailer |
| [Agentic Architecture & Orchestration](wiki/tasks/1-agentic-architecture) | [Task-2 - Coordinator subagent orchestration](tasks/agentic-architecture/task-2-coordinator-subagent-orchestration/README.md) | A research coordinator deciding whether to stay remote-first |
| [Agentic Architecture & Orchestration](wiki/tasks/1-agentic-architecture) | [Task-3 - Subagent invocation context passing](tasks/agentic-architecture/task-3-subagent-invocation-context-passing/README.md) | A trip-planning coordinator building a Lisbon travel itinerary |
| [Agentic Architecture & Orchestration](wiki/tasks/1-agentic-architecture) | [Task-4 - Multi step enforcement handoff](tasks/agentic-architecture/task-4-multi-step-enforcement-handoff/README.md) | An IT helpdesk agent granting system access requests |
| [Agentic Architecture & Orchestration](wiki/tasks/1-agentic-architecture) | [Task-5 - Hooks data normalization](tasks/agentic-architecture/task-5-hooks-data-normalization/README.md) | A shipment-tracking desk across multiple mock carrier systems |
| [Agentic Architecture & Orchestration](wiki/tasks/1-agentic-architecture) | [Task-6 - Task decomposition strategies](tasks/agentic-architecture/task-6-task-decomposition-strategies/README.md) | A manufacturing quality-control coordinator choosing decomposition strategy |
| [Agentic Architecture & Orchestration](wiki/tasks/1-agentic-architecture) | [Task-7 - Session resumption forking](tasks/agentic-architecture/task-7-session-resumption-forking/README.md) | A legacy-codebase migration coordinator managing resumable, forkable sessions |
| [Tool Design & MCP Integration](wiki/tasks/2-tool-design-mcp) | [Task-1 - Tool interface clarity boundaries](tasks/tool-design-mcp/task-1-tool-interface-clarity-boundaries/README.md) | A dev-workflow MCP server fetching user stories and planning implementation work |
| [Tool Design & MCP Integration](wiki/tasks/2-tool-design-mcp) | [Task-2 - Structured error responses](tasks/tool-design-mcp/task-2-structured-error-responses/README.md) | A warehouse-fulfillment MCP server exercising every error category |
| [Tool Design & MCP Integration](wiki/tasks/2-tool-design-mcp) | [Task-3 - Tool distribution and choice](tasks/tool-design-mcp/task-3-tool-distribution-and-choice/README.md) | An insurance-claims-desk MCP server orchestrating role-scoped subagents |
| [Tool Design & MCP Integration](wiki/tasks/2-tool-design-mcp) | [Task-4 - MCP server integration](tasks/tool-design-mcp/task-4-mcp-server-integration/README.md) | An internal engineering docs/runbooks MCP server using project-scoped config |
| [Claude Code Configuration & Workflows](wiki/tasks/3-claude-code-workflows) | [Task-1 - CLAUDE.md hierarchy scoping](tasks/claude-code-workflows/task-1-claude-md-hierarchy-scoping/README.md) | A fintech billing monorepo with per-package CLAUDE.md conventions |
| [Claude Code Configuration & Workflows](wiki/tasks/3-claude-code-workflows) | [Task-2 - Slash commands and skills](tasks/claude-code-workflows/task-2-slash-commands-and-skills/README.md) | A docs publishing monorepo with a project-scoped command and three configured skills |
| [Claude Code Configuration & Workflows](wiki/tasks/3-claude-code-workflows) | [Task-3 - Path specific rules](tasks/claude-code-workflows/task-3-path-specific-rules/README.md) | A cross-platform mobile monorepo with a glob-scoped localization convention rule |

## Repository Layout

- `wiki/exam-guide.pdf` — the certification exam guide (source material, do not edit).
- `wiki/tasks/` — one Markdown file per domain (`1-agentic-architecture.md`, `2-tool-design-mcp.md`, `3-claude-code-workflows.md`, `4-prompt-engineering.md`, `5-context-management.md`), each broken into numbered `### Task Statement X.Y` sections with `Knowledge of` / `Skills in` bullets, plus `6-preparation-tasks.md` listing the tasks end to end. Treat these as reference material — quote from them, don't edit them as part of building a task.
- `tasks/` — the practical implementations, one subfolder per domain, one folder per task inside that (see naming convention below).
- `common/` — the shared Python package (Anthropic client setup, the generic agentic tool-use loop, structured tool-error helpers, the shared formatted-JSON logging primitive, the MCP tool-call logging wrapper) reused across tasks. Installed editable into the root `uv` project, so any task script can `from common.x import y` regardless of nesting depth.
- `logs/` — formatted (pretty-printed) JSON transcripts, one file per run, entries separated by a blank line: `logs/*.jsonl` from `common/agent_loop.py`'s agentic loop, `logs/mcp/*.jsonl` from `common/mcp_logging.py`'s MCP tool-call wrapper, `logs/sessions/*.json` from `common/session_store.py`.
- `.claude/rules/` — topic-specific rule files that only load when working under a matching path (via YAML frontmatter `paths:` globs), instead of bloating this always-loaded file. See `.claude/rules/mcp-server-tasks.md` for the MCP-task attach/logging conventions.

## Task Naming & Folder Convention

Each task lives at `tasks/<domain-slug>/task-<N>-<kebab-slug>/`, where:

- `<N>` is the second number of the Task Statement it covers within that domain — Task Statement `X.N` → `task-<N>` (e.g. Task Statement 1.2 → `task-2`). Numbering restarts at 1 within each domain's folder, so a second domain growing its own tasks gets its own `task-1`, `task-2`, ... independent of Domain 1's.
- `<domain-slug>` is the slug of the domain the task belongs to.
- `<kebab-slug>` is a short kebab-case rendering of the task's **type** — the architecture pattern/mechanism it demonstrates (e.g. `multi-tool-agent-escalation`, `coordinator-subagent-orchestration`, `hooks-data-normalization`) — never the fictional scenario/topic (e.g. not `it-access-helpdesk` or `multi-carrier-shipment-tracking`). The scenario only ever appears in the Implemented Tasks table's **Topic** column and the task's own README `# Subject` section — it must never leak into the folder name, since the folder should read the same regardless of which scenario a task happens to use.

Domain slugs (fixed — do not invent new ones):

| Domain | Slug |
|---|---|
| 1 – Agentic Architecture & Orchestration | `agentic-architecture` |
| 2 – Tool Design & MCP Integration | `tool-design-mcp` |
| 3 – Claude Code Configuration & Workflows | `claude-code-workflows` |
| 4 – Prompt Engineering & Structured Output | `prompt-engineering` |
| 5 – Context Management & Reliability | `context-management` |

Every task folder must contain a `README.md` documenting which task statement(s) it covers and mapping each `Knowledge of`/`Skills in` bullet to the file (by name only, never a line number/range — those drift) plus a pasted code snippet demonstrating it (see [`tasks/agentic-architecture/task-1-multi-tool-agent-escalation/README.md`](tasks/agentic-architecture/task-1-multi-tool-agent-escalation/README.md) for the canonical example). Code should be split into small per-concern modules (e.g. `main.py` entry point, `tools.py` schemas/implementations, `policy.py`/`normalize.py` hooks, `data.py` mock data) and reuse `common/` rather than duplicating client setup, the agentic loop, or error-shaping logic. Only add to `common/` when a capability is genuinely reusable across tasks, not task-specific logic.

Use the `new-task` skill (`.claude/skills/new-task/SKILL.md`) to scaffold a new task consistent with these conventions.

## Implementation Conventions

When building tasks, use the Anthropic SDK (`@anthropic-ai/sdk` for Node.js or `anthropic` for Python). Default to the latest capable model (`claude-sonnet-4-6` or newer).

Invoke the `/claude-api` skill before writing any Anthropic SDK code — it loads current model IDs, pricing, and API patterns so you don't rely on stale training data.

### Agentic loop pattern

Terminate loops on `stop_reason === "end_turn"`, continue on `"tool_use"`. Never use arbitrary iteration caps as the primary stopping mechanism or parse assistant text content as a completion indicator.

### Structured output

Use `tool_use` with a JSON schema for guaranteed schema-compliant output. Set `tool_choice: { type: "tool", name: "..." }` to force a specific extractor; use `tool_choice: "any"` when the document type is unknown. Do not rely on `JSON.parse` of raw assistant text.

### MCP server config

- Project-shared servers → `.mcp.json` (committed, use `${ENV_VAR}` expansion for credentials)
- Personal/experimental servers → `~/.claude.json` (not committed)

See `.claude/rules/mcp-server-tasks.md` for how to register/attach an MCP server task's tools with local Claude Code and the shared logging convention — that guidance only loads when actually working under `tasks/tool-design-mcp/`, rather than every session.

### Error responses from tools

Return structured metadata: `errorCategory` (`transient` | `validation` | `permission`), `isRetryable` boolean, and a human-readable description. Never return a generic `"Operation failed"` string.
