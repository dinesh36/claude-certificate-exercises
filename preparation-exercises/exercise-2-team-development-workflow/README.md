# Preparation Exercise 2: Configure Claude Code for a Team Development Workflow

> **Objective:** Practice configuring CLAUDE.md hierarchies, custom slash commands, path-specific rules, and MCP server integration for a multi-developer project.
> **Domains reinforced:** [Domain 3](../../wiki/tasks/3-claude-code-workflows) (Claude Code Configuration & Workflows), [Domain 2](../../wiki/tasks/2-tool-design-mcp) (Tool Design & MCP Integration)

Source: [`wiki/tasks/6-preparation-exercises.md`](../../wiki/tasks/6-preparation-exercises.md), Exercise 2.

---

## Status: Fully covered

Every step below has a direct, near-1:1 implemented task — no new implementation needed.

## How each step is covered

- **Step 1 — Create a project-level CLAUDE.md with universal coding standards and testing conventions; verify project-level instructions are consistently applied across team members** — [`tasks/claude-code-workflows/task-1-claude-md-hierarchy-scoping`](../../tasks/claude-code-workflows/task-1-claude-md-hierarchy-scoping/README.md)

  A fintech billing monorepo demonstrating the full user-level/project-level/directory-level hierarchy, `@import` modularity, and diagnosing a hierarchy misconfiguration (a teammate's rules not applying because they landed in a personal `~/.claude/CLAUDE.md` instead of the tracked project config) via `/memory`.

- **Step 2 — Create `.claude/rules/` files with YAML frontmatter glob patterns for different code areas; verify rules load only when editing matching files** — [`tasks/claude-code-workflows/task-3-path-specific-rules`](../../tasks/claude-code-workflows/task-3-path-specific-rules/README.md)

  ```yaml
  ---
  paths:
    - "**/*.strings"
    - "**/strings.xml"
  ---
  ```

  A cross-platform mobile monorepo where one glob-scoped rule applies a localization-key convention across `ios/`, `android/`, and `shared/` trees alike, verified live to apply to matching files and not to unrelated ones in the same directory.

- **Step 3 — Create a project-scoped skill in `.claude/skills/` with `context: fork` and `allowed-tools` restrictions; verify it runs in isolation without polluting the main conversation** — [`tasks/claude-code-workflows/task-2-slash-commands-and-skills`](../../tasks/claude-code-workflows/task-2-slash-commands-and-skills/README.md)

  ```yaml
  # content-audit/SKILL.md
  context: fork
  # api-ref-sync/SKILL.md
  allowed-tools: Read, Grep, Glob
  # new-page/SKILL.md
  argument-hint: <page-slug>
  ```

  Also covers the project-scoped `/publish-check` slash command (step's "team-wide availability via version control" angle) and the personal-skill-variant (`~/.claude/skills/`) diagnostic.

- **Step 4 — Configure an MCP server in `.mcp.json` with environment variable expansion for credentials; add a personal experimental MCP server in `~/.claude.json` and verify both are available simultaneously** — [`tasks/tool-design-mcp/task-4-mcp-server-integration`](../../tasks/tool-design-mcp/task-4-mcp-server-integration/README.md)

  ```json
  {
    "mcpServers": {
      "engineering-docs": {
        "type": "stdio",
        "command": "uv",
        "args": ["run", "server.py"],
        "env": { "DOCS_API_KEY": "${DOCS_API_KEY}" }
      }
    }
  }
  ```

  Verified live: this project-scoped server coexists with three other already-registered MCP servers (`dev-workflow-assistant`, `warehouse-fulfillment`, `insurance-claims-desk`), all discovered and available at once. The task also separately walks through registering a personal experimental server at **user** scope (`~/.claude.json`, available from any directory) alongside it.

- **Step 5 — Test plan mode versus direct execution on tasks of varying complexity: a single-file bug fix, a multi-file library migration, and a new feature with multiple valid implementation approaches** — [`tasks/claude-code-workflows/task-4-plan-mode-vs-direct-execution`](../../tasks/claude-code-workflows/task-4-plan-mode-vs-direct-execution/README.md)

  A small e-commerce checkout service with a deliberate complexity gradient: a one-line case-sensitivity fix (direct execution, verified live as a single `Edit`), a five-file synchronous-to-event-driven checkout restructuring (plan mode — real competing architectural approaches), and an open-ended `LegacyCart` reference search (the `Explore` subagent).
