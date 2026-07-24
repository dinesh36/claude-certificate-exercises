---
paths:
  - "tasks/tool-design-mcp/**"
---

# MCP Server Tasks — attaching and logging conventions

Applies to every **MCP Server Task** under `tasks/tool-design-mcp/` (see `.claude/skills/new-task/categories/mcp-server-tasks.md`) — each of these is a real MCP server, not a script.

**Exception:** `task-5-built-in-tool-selection` (and any future **Built-in Tool Task** — see `.claude/skills/new-task/categories/built-in-tool-tasks.md`) is not an MCP server at all. It uses its own hook-based tool-call logging instead — see that task's own README for how it works. None of this file's `claude mcp add`/logging guidance applies to it.

## Attaching a task's MCP server to local Claude Code

**Check that task's own `README.md`** (its `# How to connect and run` section) for the exact `claude mcp add` command — the server name and folder differ per task, so this file doesn't repeat them. Don't guess or reconstruct the command from another task's README.

- Always register with `--directory "$(pwd)"` baked in (run the command from inside the task folder), not the bare relative `uv run server.py` — without it, the stored command only resolves when Claude Code happens to spawn it with that exact folder as the subprocess's cwd, so `claude mcp list` reports `✘ Failed to connect` from anywhere else even though nothing is actually broken.
- Once registered and verified, **leave it attached** — don't `claude mcp remove` it after testing. The point of registering is that it's ready to use without re-registering every time.
- Editing the server's code afterward doesn't retroactively update an already-registered, already-running connection: a Claude Code session started before the edit keeps talking to the process it already spawned. Whenever a task's MCP server code changes, **re-attach it** (`claude mcp remove <name>` then the `claude mcp add` command from the README again) so the registration — and any session started after that point — reflects the latest code.

## Logging convention

Wrap every MCP tool implementation with `common/mcp_logging.py`'s `logged_tool(server_name)` decorator (stacked directly under `@mcp.tool()`) — the MCP counterpart to `common/agent_loop.py`'s own formatted-JSON request logging. It logs each call's server name, tool name, input parameters, and either its result or its raised error to `logs/mcp/`.
