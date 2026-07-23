# [Claude Certified Architect – Foundations](https://anthropic-partners.skilljar.com/claude-certified-architect-foundations-certification)

According to this [exam guide](./wiki/exam-guide.pdf) claude suggested few tasks here, This repository contains the respective task implementation 

# Tasks

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

# Setup

This repository uses a single [uv](https://docs.astral.sh/uv/) project at the root for all tasks — dependencies and the shared [`common/`](./common) package are managed here, not per task.

1. Add your `ANTHROPIC_API_KEY` to a `.env` file at the repository root (gitignored).
2. Run any task from the repository root, e.g.:

   ```bash
   uv run tasks/agentic-architecture/task-1-multi-tool-agent-escalation/main.py
   ```