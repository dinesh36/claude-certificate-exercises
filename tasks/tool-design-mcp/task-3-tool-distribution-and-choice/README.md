# Task Statement 2.3: Distribute tools appropriately across agents and configure tool choice
## Knowledge of
- The principle that giving an agent access to too many tools (e.g., 18 instead of 4–5) degrades tool selection reliability by increasing decision complexity
- Why agents with tools outside their specialization tend to misuse them (e.g., a synthesis agent attempting web searches)
- Scoped tool access: giving agents only the tools needed for their role, with limited cross-role tools for specific high-frequency needs
- tool_choice configuration options: "auto", "any", and forced tool selection ({"type": "tool", "name": "..."})
## Skills in
- Restricting each subagent's tool set to those relevant to its role, preventing cross-specialization misuse
- Replacing generic tools with constrained alternatives (e.g., replacing fetch_url with load_document that validates document URLs)
- Providing scoped cross-role tools for high-frequency needs (e.g., a verify_fact tool for the synthesis agent) while routing complex cases through the coordinator
- Using tool_choice forced selection to ensure a specific tool is called first (e.g., forcing extract_metadata before enrichment tools), then processing subsequent steps in follow-up turns
- Setting tool_choice: "any" to guarantee the model calls a tool rather than returning conversational text

---

# Subject
An insurance-claims-desk MCP server. Its two MCP-exposed tools each run their own internal Anthropic API subagent pipeline.

That's a hybrid on purpose. `tool_choice` has no MCP-protocol equivalent — it's a Messages API parameter that Claude Code's own harness sets when *it* calls the model. An MCP server's tool definitions can't express it. So this server puts real Anthropic API calls inside its own MCP tools.

Tool distribution across agents shows up at two layers:
- **Inside the pipeline** — Anthropic-API subagents, each scoped to its own internal tool list.
- **At the Claude Code layer** — real `.claude/agents/*.md` subagents, each scoped to one specific MCP tool.

What each piece does:
- `process_claim` runs three role-scoped subagents in sequence: intake, coverage assessment, then customer-letter synthesis. Each one only gets the tools its own role needs — the synthesis subagent never gets policy-lookup tools, and the intake subagent never gets drafting tools.
- The intake subagent's first tool call is **forced** (`extract_claim_metadata`). Its follow-up turns are free to choose an enrichment tool.
- `classify_claim` runs a single subagent with `tool_choice: "any"` — it must call a tool, never just reply in prose.
- The synthesis subagent gets exactly one narrow cross-role tool (`verify_claim_fact`, a single-fact spot-check), not full read access to policy/coverage data. Verified live: it correctly refuses to guess a decision when the file doesn't support one yet.
- Two real Claude Code subagents (`claims-processor`, `claims-triage`) are each scoped to exactly one of the server's two MCP tools. `claims-triage` literally cannot call `process_claim`, and vice versa.

---

# How to connect and run
This task is a real MCP server, not a script you `uv run` directly — Claude Code is the client that talks to it.

Unlike task-1/task-2 in this domain, its tool *implementations* also make their own internal Anthropic API calls (see `pipeline.py`). The server has both an MCP-server side and an agentic-loop side.

1. **Register the server** (run from inside this task folder, so it's scoped to just this task):
   ```bash
   cd tasks/tool-design-mcp/task-3-tool-distribution-and-choice
   claude mcp add --transport stdio insurance-claims-desk -- uv run --directory "$(pwd)" server.py
   ```
   This uses the default **local** scope, stored in `~/.claude.json` keyed to this exact directory. The `--directory "$(pwd)"` bakes in the absolute path, so the registration also connects from other directories (see `.claude/rules/mcp-server-tasks.md`).

2. **Verify it connected:**
   ```bash
   claude mcp list
   ```
   `insurance-claims-desk` should show as `✔ Connected`.

3. **Start a Claude Code session from this same directory** and try these prompts:

   ```
   Process insurance claim CLAIM-1001 through the claims desk.
   ```
   CLAIM-1001 is missing a required document (photos). Expected, verified live:
   - Intake flags the missing document and declines to assess coverage or draft a letter — "outside my intake role."
   - The assessor confirms coverage but flags the missing document as blocking.
   - The synthesis subagent **refuses to force an approve/deny/partial decision**, since none is accurate yet. It asks the coordinator to confirm a request-for-documents letter instead.

   ```
   Process insurance claim CLAIM-1002 through the claims desk.
   ```
   CLAIM-1002 has every required document, and its claimed amount ($18,500) exceeds its policy limit ($10,000). Expected, verified live: a clean "partial" decision letter citing a $9,000 payout ($10,000 limit − $1,000 deductible). The math and decision were correct.

   ```
   Classify the urgency of claim CLAIM-1002.
   ```
   Expected, verified live: a `high` urgency classification, always backed by an actual `classify_claim_urgency` tool call — never a bare conversational guess.

4. **Leave the server registered.** Once verified, keep it attached rather than removing it. If you edit any file in this task later, re-attach it: `claude mcp remove insurance-claims-desk`, then the `claude mcp add` command above again.

5. **Try the two real Claude Code subagents** (`.claude/agents/claims-processor.md`, `.claude/agents/claims-triage.md`). These are only discovered when Claude Code's working directory is this task folder — same as the MCP registration above.

   ```
   Use a subagent to process CLAIM-1001.
   ```
   Should delegate to `claims-processor`. It can only call `process_claim` — it has no way to call `classify_claim`.

   ```
   Use a subagent to check the urgency of CLAIM-1002.
   ```
   Should delegate to `claims-triage`. It can only call `classify_claim` — it has no way to call `process_claim`.

   ```
   Use a subagent - claims-triage to process CLAIM-1001.
   ```
   This one deliberately asks a triage-only subagent to do a processing-only job. **Verified live** — `claims-triage` did not process the claim. Its `tools:` allowlist only has `classify_claim`, so `process_claim` isn't a call it's even capable of making. It fell back to the one tool it does have and replied:

   > "CLAIM-1001 triaged as Medium urgency — flagged based on a claimed amount of $4,200. Let me know if you'd like it fully processed (coverage assessment + customer letter) via the claims-processor subagent."

   That's the task statement's "preventing cross-specialization misuse" bullet made concrete. The prompt explicitly asked for the wrong job. What stopped it wasn't a system-prompt instruction the model could ignore — it was a Claude-Code-enforced tool allowlist. It didn't guess, didn't fabricate a processing result, and correctly pointed to the right subagent instead.

**Verification note:**
- The MCP server itself is confirmed connected — `claude mcp list` shows `✔ Connected`.
- Every `process_claim`/`classify_claim` scenario in step 3 was verified by calling them directly as Python functions — the exact same code path Claude Code invokes via the MCP protocol.
- The subagent-boundary test in step 5 was verified through an actual live Claude Code session, and reproduced the expected refusal exactly.

---

# Implementation Info
> `server.py` exposes two MCP tools (`process_claim`, `classify_claim`), each wrapped in `common/mcp_logging.py`'s `logged_tool`. Both raise `common/errors.py`'s `StructuredToolError` for an unknown claim ID before any API call runs.
>
> `pipeline.py` orchestrates four isolated subagent calls via `common/agent_loop.py`'s `run_tool_loop`, each scoped to one of `internal_tools.py`'s four role-specific tool lists (`INTAKE_TOOLS`, `ASSESSOR_TOOLS`, `SYNTHESIS_TOOLS`, `CLASSIFY_TOOLS`). `data.py` holds the mock claim/policy data.
>
> `.claude/agents/claims-processor.md` and `.claude/agents/claims-triage.md` are real Claude Code subagents, each scoped to one of the two MCP tools — the same tool-distribution idea, one layer up, using Claude Code's own feature instead of a simulated one.

## How each Task Info item is covered:

- **The principle that giving an agent access to too many tools degrades tool selection reliability by increasing decision complexity** — `internal_tools.py`

  ```python
  INTAKE_TOOLS = [...]      # 2 tools
  ASSESSOR_TOOLS = [...]    # 2 tools
  SYNTHESIS_TOOLS = [...]   # 2 tools
  CLASSIFY_TOOLS = [...]    # 1 tool
  ```

  Four separate lists of 1-2 tools each, instead of one shared list of all 7 internal tools. Each subagent only ever sees the couple of tools its own role could plausibly need.

- **Why agents with tools outside their specialization tend to misuse them (e.g., a synthesis agent attempting web searches)** — verified live, `README.md`

  Processing CLAIM-1001 (missing a document) showed the inverse proof. The synthesis subagent's tools are `verify_claim_fact` and `draft_customer_letter` only, so it couldn't improvise a coverage lookup. It said the letter "isn't ready" and refused to guess an approve/deny/partial decision — asking the coordinator to confirm the next step instead of misusing `draft_customer_letter` to force an outcome the file didn't support.

- **Scoped tool access: giving agents only the tools needed for their role, with limited cross-role tools for specific high-frequency needs** — `internal_tools.py`

  ```python
  SYNTHESIS_TOOLS = [
      {"schema": {"name": "verify_claim_fact", ...}, "implementation": _verify_claim_fact},
      {"schema": {"name": "draft_customer_letter", ...}, "implementation": _draft_customer_letter},
  ]
  ```

  The synthesis subagent's only "lookup" capability is `verify_claim_fact` — a narrow, single-fact spot-check (see the cross-role bullet below). It doesn't get `lookup_policy`/`check_coverage`; those stay exclusive to the assessor.

- **tool_choice configuration options: "auto", "any", and forced tool selection ({"type": "tool", "name": "..."})** — `common/agent_loop.py`

  ```python
  create_kwargs = dict(model=model, max_tokens=max_tokens, system=system, tools=tool_schemas, messages=messages)
  if is_first_turn and initial_tool_choice is not None:
      create_kwargs["tool_choice"] = initial_tool_choice
  is_first_turn = False
  ```

  `run_tool_loop` gained an `initial_tool_choice` parameter. It's backward compatible — every other task omits it and gets Anthropic's default `"auto"` on every turn. When given, it only applies to the first API call in a loop; every turn after that reverts to `"auto"`.

- **Restricting each subagent's tool set to those relevant to its role, preventing cross-specialization misuse** — `pipeline.py`, `.claude/agents/claims-processor.md`, `.claude/agents/claims-triage.md`

  ```python
  def run_assessment(claim_id: str, intake_summary: str) -> str:
      result = run_tool_loop(
          ...
          system=(
              "You are the COVERAGE ASSESSOR ... You only have policy "
              "lookup and coverage-check tools — you cannot extract intake "
              "metadata or draft customer letters; those are different "
              "specialists' jobs. ..."
          ),
          tools=ASSESSOR_TOOLS,
          ...
      )
  ```

  Every one of the four subagent functions in `pipeline.py` passes a different, role-scoped `tools=` list — never `internal_tools`' full set.

  The same idea shows up one layer up, using the real Claude Code subagent feature instead of a simulated one:

  ```markdown
  ---
  name: claims-triage
  description: Quickly classify an insurance claim's urgency (low/medium/high) without running the full processing pipeline. Use this for a fast triage check, not for approving, denying, or drafting anything.
  tools: mcp__insurance-claims-desk__classify_claim
  ---
  ```

  `claims-triage`'s `tools:` frontmatter is a Claude-Code-enforced allowlist of exactly one MCP tool. It cannot call `process_claim`, even if a prompt tries to steer it there — and `claims-processor`'s frontmatter applies the same restriction in reverse. The difference from `pipeline.py`'s scoping: this restriction is enforced by Claude Code's own permission layer, before the subagent ever runs — not just by which tools happen to be in a given `run_tool_loop` call.

  Verified live with a prompt that deliberately asks for the wrong job: `Use a subagent - claims-triage to process CLAIM-1001.`
  - `claims-triage` did not process the claim.
  - Its allowlist has no `process_claim`, so it fell back to the one tool it does have.
  - It replied: *"CLAIM-1001 triaged as Medium urgency — flagged based on a claimed amount of $4,200. Let me know if you'd like it fully processed (coverage assessment + customer letter) via the claims-processor subagent."*
  - No fabricated processing result, no misuse of `classify_claim` to fake a decision — just a correct refusal plus a pointer to the right subagent.

- **Replacing generic tools with constrained alternatives (e.g., replacing fetch_url with load_document that validates document URLs)** — `internal_tools.py`

  ```python
  def _verify_claim_fact(claim_id: str, fact: str) -> dict:
      if fact not in _VERIFIABLE_FACTS:
          return tool_error(
              "validation",
              False,
              f"'{fact}' isn't a fact this tool can verify. Known facts: {', '.join(_VERIFIABLE_FACTS)}. "
              "For anything else, route the question back through the coordinator instead of guessing.",
          )
  ```

  `verify_claim_fact` is the constrained alternative to a generic "get any field" lookup tool. It checks `fact` against an explicit allowlist and refuses (with a pointer to escalate) rather than returning arbitrary claim data — the same idea as the wiki's own `fetch_url` → `load_document` example.

- **Providing scoped cross-role tools for high-frequency needs (e.g., a verify_fact tool for the synthesis agent) while routing complex cases through the coordinator** — `pipeline.py`

  ```python
  "The one exception is verify_claim_fact, a narrow tool for double-checking "
  "a single already-known fact before it goes in a letter."
  ```

  The synthesis subagent's own system prompt names `verify_claim_fact` as the one deliberate exception to its otherwise read-nothing role — exactly the "verify_fact tool for the synthesis agent" example from the task statement. It's also told to route anything else back to the coordinator, which is what it did live when CLAIM-1001's missing document made a decision unsupportable.

- **Using tool_choice forced selection to ensure a specific tool is called first (e.g., forcing extract_metadata before enrichment tools), then processing subsequent steps in follow-up turns** — `pipeline.py`

  ```python
  def run_intake(claim_id: str) -> str:
      result = run_tool_loop(
          ...
          tools=INTAKE_TOOLS,
          user_message=f"Process intake for claim {claim_id}.",
          initial_tool_choice={"type": "tool", "name": "extract_claim_metadata"},
      )
  ```

  `run_intake` forces `extract_claim_metadata` on the first turn — verified live, every run called it first. The loop's second turn is free (`tool_choice` omitted), and calls the enrichment tool `flag_missing_documents` — which it did in both live runs.

- **Setting tool_choice: "any" to guarantee the model calls a tool rather than returning conversational text** — `pipeline.py`

  ```python
  def run_classification(claim_id: str) -> str:
      result = run_tool_loop(
          ...
          tools=CLASSIFY_TOOLS,
          user_message=f"Classify the urgency of claim {claim_id}.",
          initial_tool_choice={"type": "any"},
      )
  ```

  Verified live: `classify_claim("CLAIM-1002")` returned a `high` classification backed by an actual `classify_claim_urgency` tool call. `tool_choice: "any"` is what guarantees that call happens, instead of the model just answering "this seems urgent" in prose.
