# Task Statement 2.1: Design effective tool interfaces with clear descriptions and boundaries
## Knowledge of
- Tool descriptions as the primary mechanism LLMs use for tool selection; minimal descriptions lead to unreliable selection among similar tools
- The importance of including input formats, example queries, edge cases, and boundary explanations in tool descriptions
- How ambiguous or overlapping tool descriptions cause misrouting (e.g., analyze_content vs analyze_document with near-identical descriptions)
- The impact of system prompt wording on tool selection: keyword-sensitive instructions can create unintended tool associations
## Skills in
- Writing tool descriptions that clearly differentiate each tool's purpose, expected inputs, outputs, and when to use it versus similar alternatives
- Renaming tools and updating descriptions to eliminate functional overlap (e.g., renaming analyze_content to extract_web_results with a web-specific description)
- Splitting generic tools into purpose-specific tools with defined input/output contracts (e.g., splitting a generic analyze_document into extract_data_points, summarize_content, and verify_claim_against_source)
- Reviewing system prompts for keyword-sensitive instructions that might override well-written tool descriptions

---

# Subject
A dev-workflow MCP server that fetches user stories and bug tickets from two separate mock trackers and turns a fetched story into a development plan.
- It replaces an originally ambiguous `get_item(id)` tool with two domain-specific tools: `fetch_user_story` and `fetch_bug_ticket`. The old tool could return either a story or a bug ticket depending on what happened to live at that ID, and regularly misrouted "the export bug" to the story tracker and vice versa.
- It also replaces an originally generic `create_plan(id)` tool with three purpose-specific tools: `identify_story_risks`, `estimate_story_effort`, and `generate_dev_plan`. The old tool vaguely "did something plan-related" for any ID. Each new tool has a defined input/output contract and an explicit cross-reference to its siblings.

---

# How to connect and run
This task is a real MCP server, not a script you `uv run` directly — Claude Code is the client that talks to it.

1. **Register the server** (run from inside this task folder, so it's scoped to just this task rather than every project on your machine):
   ```bash
   cd tasks/tool-design-mcp/task-1-tool-interface-clarity-boundaries
   claude mcp add --transport stdio dev-workflow-assistant -- uv run --directory "$(pwd)" server.py
   ```
   This uses the default **local** scope, stored in `~/.claude.json` keyed to this exact directory. It won't appear in any other project, and won't touch this repo's own root `.mcp.json`.

   The `--directory "$(pwd)"` bakes the absolute task-folder path into the registered command itself. Without it, the stored command is the bare relative `uv run server.py`, which only resolves when Claude Code happens to spawn it with this folder as the process's cwd. `claude mcp list` would then report `✘ Failed to connect` from anywhere else — even though the registration itself is fine.
2. **Verify it connected:**
   ```bash
   claude mcp list
   ```
   `dev-workflow-assistant` should show as `✔ Connected`.
3. **Start a Claude Code session from this same directory** and try these prompts — each is designed to exercise one tool-selection decision the task statement is about:
   ```
   Can you pull up the details for the Safari export bug, ticket BUG-501?
   ```
   Should call `fetch_bug_ticket`, not `fetch_user_story`. The "bug" framing and `BUG-` ID are the disambiguating signal. Verified live: returned the ticket's repro steps and severity.
   ```
   What's the CSV export story, STORY-101, about?
   ```
   Should call `fetch_user_story`, not `fetch_bug_ticket`. The "story" framing and `STORY-` ID disambiguate the other way. Verified live: returned the story's description and acceptance criteria.
   ```
   How big of an effort is STORY-102, roughly?
   ```
   Should call `estimate_story_effort` only — not `generate_dev_plan`. A sizing question shouldn't produce a task breakdown. Verified live: returned only a size ("S") and rationale, no task list.
   ```
   Break STORY-101 down into an implementation plan for the dev team.
   ```
   Should call `generate_dev_plan` — not `estimate_story_effort`. Verified live: returned an ordered task list derived from the story's acceptance criteria, with no size/estimate mixed in.
4. **Remove the server when done** (optional cleanup):
   ```bash
   claude mcp remove dev-workflow-assistant
   ```

---

# Implementation Info
> `server.py` creates the FastMCP instance and defines all five tools directly on it with `@mcp.tool()`; `data.py` holds the two separate mock trackers (`USER_STORIES`, `BUG_TICKETS`) the tools read from.
## How each Task Info item is covered:
- **Tool descriptions as the primary mechanism LLMs use for tool selection; minimal descriptions lead to unreliable selection among similar tools** — `server.py`

  ```python
  @mcp.tool()
  def fetch_user_story(story_id: str) -> dict:
      """Fetch a feature/user story from the product backlog by its story ID.

      Use this for anything framed as a FEATURE REQUEST or USER STORY — new
      functionality the team is planning to build (e.g. "the CSV export
      story"). Do NOT use this for bug reports; call fetch_bug_ticket instead
      for anything framed as broken, unresponsive, or not working as expected.
      ...
      """
  ```

  FastMCP uses each tool's docstring as its description. Verified live: a "the Safari export bug" prompt correctly triggered `fetch_bug_ticket`, and a "the CSV export story" prompt correctly triggered `fetch_user_story` — entirely on the strength of this wording.

- **The importance of including input formats, example queries, edge cases, and boundary explanations in tool descriptions** — `server.py`

  ```python
  def fetch_user_story(story_id: str) -> dict:
      """Fetch a feature/user story from the product backlog by its story ID.

      Use this for anything framed as a FEATURE REQUEST or USER STORY — new
      functionality the team is planning to build (e.g. "the CSV export
      story"). Do NOT use this for bug reports; call fetch_bug_ticket instead
      for anything framed as broken, unresponsive, or not working as expected.

      Args:
          story_id: Exact story ID, e.g. "STORY-101". Story IDs always start
              with "STORY-".

      Returns:
          A dict with title, description, acceptance_criteria (list), and
          dependencies (list of blocking items, empty if none).

      Raises:
          ValueError: if story_id isn't a known story. If it looks like a bug
              ticket ID instead, the error names fetch_bug_ticket as the
              correct tool to call.
      """
  ```

  Pasted in full, the docstring states all four elements the bullet calls for:
  - The input format (`"STORY-101"`)
  - An example query ("the CSV export story")
  - The output shape
  - The edge case/boundary (what happens on an unknown or wrong-kind ID)

- **How ambiguous or overlapping tool descriptions cause misrouting (e.g., analyze_content vs analyze_document with near-identical descriptions)** — `server.py` (before/after, documented here)

  The server's own module docstring records the "before" this replaced:
  > "Replaces an originally ambiguous get_item(id) tool (which could return either a story or a bug ticket depending on what happened to be at that ID, and regularly misrouted 'the export bug' to the story tracker and vice versa)..."

  A single `get_item(id)` with a generic description gives the model no signal to distinguish "the export bug" from "the export story" — both are plausible for the same vague tool. Splitting it into `fetch_user_story`/`fetch_bug_ticket`, each naming its own domain explicitly, is the fix. Verified live against both framings.

- **The impact of system prompt wording on tool selection: keyword-sensitive instructions can create unintended tool associations** — analysis (no code change; Claude Code's own system prompt isn't something this task's server controls)

  A system-prompt instruction like *"Always use fetch_user_story whenever the user mentions an ID"* would override this server's careful per-tool boundaries. It would push every `BUG-*` lookup through `fetch_user_story`, no matter how clearly that tool's own docstring says not to.

  The fix: never key tool routing off a single keyword (like "ID") in the system prompt. Let the tool descriptions themselves carry the disambiguating detail — the ID prefix, the framing words. Keep system-prompt instructions generic ("call the fetch tool whose description matches the request"), not prescriptive about which tool to prefer.

- **Writing tool descriptions that clearly differentiate each tool's purpose, expected inputs, outputs, and when to use it versus similar alternatives** — `server.py`

  ```python
  """Estimate a t-shirt-size effort (S/M/L) for a user story, with rationale.

  Use this when asked for a SIZE, ESTIMATE, or "how much work" a story is —
  it returns sizing only, not a task breakdown. Call generate_dev_plan
  instead when asked for the actual implementation steps.
  """
  ```

  `estimate_story_effort`'s docstring explicitly names `generate_dev_plan` as the sibling to use instead for a different kind of question. Verified live: a pure sizing prompt triggered only `estimate_story_effort`, not `generate_dev_plan` — even though both tools take the same `story_id` argument.

- **Renaming tools and updating descriptions to eliminate functional overlap (e.g., renaming analyze_content to extract_web_results with a web-specific description)** — `server.py`

  ```python
  def fetch_bug_ticket(ticket_id: str) -> dict:
      """Fetch a bug ticket from the bug tracker by its ticket ID.

      Use this for anything framed as BROKEN, UNRESPONSIVE, or NOT WORKING AS
      EXPECTED (e.g. "the Safari export bug"). Do NOT use this for new feature
      requests; call fetch_user_story instead for anything framed as a feature
      or user story.
      """
  ```

  `fetch_bug_ticket` is renamed from the original generic `get_item`, and scoped to the bug domain by name and description — exactly mirroring the wiki's own `analyze_content` → `extract_web_results` rename pattern.

- **Splitting generic tools into purpose-specific tools with defined input/output contracts (e.g., splitting a generic analyze_document into extract_data_points, summarize_content, and verify_claim_against_source)** — `server.py`

  ```python
  @mcp.tool()
  def identify_story_risks(story_id: str) -> dict: ...

  @mcp.tool()
  def estimate_story_effort(story_id: str) -> dict: ...

  @mcp.tool()
  def generate_dev_plan(story_id: str) -> dict: ...
  ```

  The original generic `create_plan(id)` is split into three tools with distinct, defined contracts:
  - `identify_story_risks` returns a `risks` list.
  - `estimate_story_effort` returns a `size`/`rationale` pair.
  - `generate_dev_plan` returns an ordered `tasks` list.

  This mirrors the wiki's `extract_data_points`/`summarize_content`/`verify_claim_against_source` split.

- **Reviewing system prompts for keyword-sensitive instructions that might override well-written tool descriptions** — analysis (see the Knowledge-of entry above)

  Reviewing a system prompt for this task means checking it never singles out one tool by a keyword the request merely happens to contain — like "ID" or "ticket." The live test above (a pure sizing prompt correctly avoiding `generate_dev_plan`) only holds because no such override was present. A prescriptive system-prompt rule could have broken it, no matter how clear the tool docstrings were.
