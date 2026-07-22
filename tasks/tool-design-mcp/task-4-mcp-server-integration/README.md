# Task Statement 2.4: Integrate MCP servers into Claude Code and agent workflows
## Knowledge of
- MCP server scoping: project-level (.mcp.json) for shared team tooling vs user-level (~/.claude.json) for personal/experimental servers
- Environment variable expansion in .mcp.json (e.g., ${GITHUB_TOKEN}) for credential management without committing secrets
- That tools from all configured MCP servers are discovered at connection time and available simultaneously to the agent
- MCP resources as a mechanism for exposing content catalogs (e.g., issue summaries, documentation hierarchies, database schemas) to reduce exploratory tool calls
## Skills in
- Configuring shared MCP servers in project-scoped .mcp.json with environment variable expansion for authentication tokens
- Configuring personal/experimental MCP servers in user-scoped ~/.claude.json
- Enhancing MCP tool descriptions to explain capabilities and outputs in detail, preventing the agent from preferring built-in tools (like Grep) over more capable MCP tools
- Choosing existing community MCP servers over custom implementations for standard integrations (e.g., Jira), reserving custom servers for team-specific workflows
- Exposing content catalogs as MCP resources to give agents visibility into available data without requiring exploratory tool calls

---

# Subject
An internal engineering docs/runbooks MCP server, registered in this repo's own project-scoped `.mcp.json` for the first time — every earlier MCP task here used *local* scope instead (also `~/.claude.json`, but tied to just that one task's own folder).
- `search_docs` and `get_doc` are regular tools. A `docs://catalog` **resource** exposes the full doc hierarchy up front, so the agent can browse it without an exploratory search call.
- The server needs a `DOCS_API_KEY` credential. `.mcp.json` references it as `${DOCS_API_KEY}`, so the actual secret never gets committed — only the reference does.
- This server coexists with three other MCP servers already registered in this repo (`dev-workflow-assistant`, `warehouse-fulfillment`, `insurance-claims-desk`). All four are discovered and available at once — nothing about adding a fourth server breaks the other three.
- This README also walks through the third scope, *user*, which none of the other tasks demonstrate — a server registered once and available in every project on your machine, not just one folder.

---

# How to connect and run
This task is a real MCP server, not a script you `uv run` directly — Claude Code is the client that talks to it.

This one is registered at **project scope** instead of the personal scope the other three MCP tasks use — but project scope is still resolved from the current directory, not the whole repo. `cd` into this task folder first, just like the other tasks:
```bash
cd tasks/tool-design-mcp/task-4-mcp-server-integration
```
The registration lives in `.mcp.json` **inside this folder**, not the repo root. It only applies when your working directory is exactly here — the same rule local-scope registrations follow, just backed by a committed file instead of `~/.claude.json`.

1. **Export a credential.** The server refuses every tool call without one:
   ```bash
   export DOCS_API_KEY=some-test-value
   ```
2. **Approve the project-scoped server**, if you haven't already, by starting a normal `claude` session from this folder. Claude Code prompts for approval the first time it sees a new server in a `.mcp.json`.
3. **Check `claude mcp list` for context, but don't trust it as proof either way:**
   ```bash
   claude mcp list
   ```
   Run this from the same folder. It should at least list `engineering-docs`.
4. **Try these prompts** — each is designed to exercise one integration decision the task statement is about:
   ```
   What sections of engineering docs are available? Check the engineering-docs catalog resource.
   ```
   Should answer directly from the `docs://catalog` resource, not a search call. Verified live: it listed all three sections (Runbooks, Standards, Onboarding), grouped exactly like the resource's own output — not a flat tool-result list.
   ```
   What runbooks do we have for database failover? Use the engineering-docs search tool.
   ```
   Should call `search_docs`, then `get_doc` for the full content. Verified live: it returned the runbook's full 4-step body, not just a title match.
   ```
   Search engineering docs for 'kubernetes'.
   ```
   Should return an empty match list, not an error. Verified live: the agent correctly reported no matches.
5. **Try it with the credential unset:**
   ```bash
   unset DOCS_API_KEY
   ```
   Then repeat the search prompt. Verified live: the agent explained that `DOCS_API_KEY` isn't set and that it needs to be exported before the search can run — it didn't retry blindly or return a generic failure.
6. **Leave the server registered.** If you edit `server.py` later, no re-registration is needed — a new Claude Code session spawns the updated code automatically, since `.mcp.json`'s command doesn't change.

---

# Implementation Info
> `server.py` creates the FastMCP instance, defines `search_docs`/`get_doc` with `@mcp.tool()`, and defines the doc catalog with `@mcp.resource("docs://catalog")`. `data.py` holds the mock doc catalog. This task's own `.mcp.json` holds the project-scoped registration with `${DOCS_API_KEY}` expansion.
## How each Task Info item is covered:
- **MCP server scoping: project-level (.mcp.json) for shared team tooling vs user-level (~/.claude.json) for personal/experimental servers** — `.mcp.json`

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

  This is the first MCP task in this repo to use project scope. `dev-workflow-assistant`, `warehouse-fulfillment`, and `insurance-claims-desk` are all local scope (`~/.claude.json`, personal to whoever registered them, tied to just their own folder). This server is different — it's meant to be shared by the whole team, so its `.mcp.json` is committed inside this task's own folder instead.

  Local scope isn't the same thing as user scope, even though both live in `~/.claude.json`. See the "Configuring personal/experimental MCP servers in user-scoped ~/.claude.json" bullet below for the actual difference, verified live.

  Project scope is still resolved from the current directory, the same as local scope — it just uses a committed file instead of a personal one. `.mcp.json` lives here, in `tasks/tool-design-mcp/task-4-mcp-server-integration/`, not the repo root. It only takes effect when a Claude Code session's working directory is exactly this folder.

- **Environment variable expansion in .mcp.json (e.g., ${GITHUB_TOKEN}) for credential management without committing secrets** — `.mcp.json`, `server.py`

  ```python
  def _require_api_key() -> None:
      api_key = os.environ.get("DOCS_API_KEY", "")
      # If ${DOCS_API_KEY} in .mcp.json's `env` block couldn't be expanded (the
      # variable was unset in the caller's shell), Claude Code passes the
      # literal, unexpanded "${DOCS_API_KEY}" text through as the value rather
      # than leaving it empty — a non-empty string that still isn't a real key.
      if not api_key or api_key.startswith("${"):
          raise StructuredToolError(...)
  ```

  `.mcp.json` only ever stores the reference `${DOCS_API_KEY}`, never a real value. Verified live twice: with the variable exported, the server works normally. With it unset, Claude Code passes the literal text `${DOCS_API_KEY}` through as the env value instead of leaving it empty — the check above catches that case too, not just a missing variable.

- **That tools from all configured MCP servers are discovered at connection time and available simultaneously to the agent** — `claude mcp list` output

  ```
  engineering-docs: ... - ⏸ Pending approval (run `claude` to approve)
  dev-workflow-assistant: ... - ✔ Connected
  warehouse-fulfillment: ... - ✔ Connected
  insurance-claims-desk: ... - ✔ Connected
  ```

  Adding this fourth server didn't touch or restart the other three. All four still list together, and their tools all worked in the same live session.
  - `engineering-docs` shows `Pending approval` here, not `Connected` — even though its tools work fine once queried (see the credential bullet above).
  - `claude mcp list`'s status column is a separate health probe. It isn't proof either way that a server's tools will actually work.
  - Don't rely on it. Try a real prompt instead.

- **MCP resources as a mechanism for exposing content catalogs (e.g., issue summaries, documentation hierarchies, database schemas) to reduce exploratory tool calls** — `server.py`

  ```python
  @mcp.resource("docs://catalog")
  def docs_catalog() -> str:
      """Full hierarchy of every doc this server knows about, grouped by section.

      Read this FIRST, before calling search_docs. It lists every doc's ID,
      title, and section in one shot. A request like "what runbooks do we have
      for on-call?" can often be answered directly from this catalog, with no
      tool call needed at all.
      """
  ```

  This is the first `@mcp.resource()` in this repo — every earlier MCP task only used `@mcp.tool()`. Verified live: asking what doc sections exist was answered straight from this resource, not from a `search_docs` call.

- **Configuring shared MCP servers in project-scoped .mcp.json with environment variable expansion for authentication tokens** — `.mcp.json`

  Same file as above. `.mcp.json` is committed to the repo, so every teammate who clones it and works in this folder gets the same server registration — they just need their own `DOCS_API_KEY` exported locally. Because the file lives inside the task folder itself, `args` is just `["run", "server.py"]` — no absolute path or `--directory` flag needed, since Claude Code already spawns the server with this folder as its working directory.

- **Configuring personal/experimental MCP servers in user-scoped ~/.claude.json** — verified live below

  Claude Code actually has three scopes, not two. Task-1, task-2, and task-3 all use **local** scope — the default, no `--scope` flag needed. Local scope is stored in `~/.claude.json`, but it's tied to one specific project directory. It's private to you, but only usable in that one folder.

  **User** scope is different. It's also stored in `~/.claude.json`, but it's available across *every* project on your machine, not just one folder. That's the scope this bullet is actually about.

  To see the difference yourself:
  ```bash
  cd tasks/tool-design-mcp/task-4-mcp-server-integration
  claude mcp add --scope user --transport stdio engineering-docs-personal-demo -- uv run --directory "$(pwd)" server.py
  ```
  Then check from a totally unrelated directory:
  ```bash
  cd /tmp
  claude mcp list
  ```
  Verified live: `engineering-docs-personal-demo` shows up here, `✔ Connected` — even from `/tmp`, nowhere near this repo. Local and project scope would never do that.

  A live query from `/tmp` worked too, calling `search_docs` and returning a real match.

  Clean up when you're done, since a user-scoped server follows you into every project from now on:
  ```bash
  claude mcp remove --scope user engineering-docs-personal-demo
  ```

- **Enhancing MCP tool descriptions to explain capabilities and outputs in detail, preventing the agent from preferring built-in tools (like Grep) over more capable MCP tools** — `server.py`

  ```python
  """Search engineering docs by title, section, and tags — not raw text grep.

  Prefer this over a local Grep/Read pass through documentation files.
  This tool understands doc structure (title, section, tags). A query
  like "database failover" matches on tags and section even if those
  exact words never appear in a doc's body text — a plain text search
  would miss that entirely.
  """
  ```

  `search_docs`'s docstring names the alternative (`Grep`/`Read`) explicitly and explains why this tool wins: it searches structured metadata (tags, section), not just raw text. A generic description ("searches documents") wouldn't give the agent a reason to prefer it over a built-in tool it already knows well.

- **Choosing existing community MCP servers over custom implementations for standard integrations (e.g., Jira), reserving custom servers for team-specific workflows** — analysis (no code — a judgment call, not a mechanism)

  This server is a reasonable custom build because it's team-specific: a fictional internal docs system with no public API and no existing community server. A real Jira or GitHub integration should use the community MCP server for that product instead of writing one from scratch — reserve custom servers for internal, team-specific systems like this one.

- **Exposing content catalogs as MCP resources to give agents visibility into available data without requiring exploratory tool calls** — same `docs://catalog` resource as above

  The catalog bullet appears in both Knowledge of and Skills in. The same resource covers both: it's the *mechanism* (Knowledge of) and this task's actual *use* of that mechanism (Skills in) — the agent doesn't need a `search_docs("")` fishing call just to see what exists.

```
const Select = (props: ) => (
  <Select {...props} />
)
```