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
