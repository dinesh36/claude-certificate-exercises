# Task Statement 1.3: Configure subagent invocation, context passing, and spawning
## Knowledge of
- The Task tool as the mechanism for spawning subagents, and the requirement that allowedTools must include "Task" for a coordinator to invoke subagents
- That subagent context must be explicitly provided in the prompt—subagents do not automatically inherit parent context or share memory between invocations
- The AgentDefinition configuration including descriptions, system prompts, and tool restrictions for each subagent type
- Fork-based session management for exploring divergent approaches from a shared analysis baseline
## Skills in
- Including complete findings from prior agents directly in the subagent's prompt (e.g., passing web search results and document analysis outputs to the synthesis subagent)
- Using structured data formats to separate content from metadata (source URLs, document names, page numbers) when passing context between agents to preserve attribution
- Spawning parallel subagents by emitting multiple Task tool calls in a single coordinator response rather than across separate turns
- Designing coordinator prompts that specify research goals and quality criteria rather than step-by-step procedural instructions, to enable subagent adaptability

---

# Task
A trip-planning coordinator pulling together what four travel blog posts say about a Lisbon trip, then optionally turning that into itinerary options.
- Reviews every relevant blog post with one isolated subagent call per post, emitted together in a single turn rather than one at a time.
- Passes the complete structured findings (claim, verbatim evidence, and which blog/author said it) into a synthesis subagent, never just IDs or paraphrased summaries.
- Only if the user actually wants an itinerary, forks the resulting destination summary into two parallel subagents exploring a budget vs. a luxury trip from the identical shared baseline.

---

# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run tasks/agentic-architecture/task-3-subagent-invocation-context-passing/main.py
```
Optionally pass a custom request as the first argument:
```bash
uv run tasks/agentic-architecture/task-3-subagent-invocation-context-passing/main.py "I'm planning a trip to Lisbon. Pull together what these blog posts say about it, and give me both a budget and a luxury itinerary option."
uv run tasks/agentic-architecture/task-3-subagent-invocation-context-passing/main.py "Just tell me what these blog posts say about Lisbon overall - I don't need a specific itinerary yet."
```
The first (default) scenario makes the coordinator emit all four `dispatch_blog_review_subagent` calls in one turn, pass the complete findings to `dispatch_synthesis_subagent`, then fork the resulting summary into two parallel `dispatch_itinerary_subagent` calls (`budget` and `luxury`) in a single later turn. The second, narrower scenario makes it stop after synthesis and never call `dispatch_itinerary_subagent` at all — the coordinator adapts to what was actually asked rather than always running the full fixed pipeline (verified live: 0 `dispatch_itinerary_subagent` calls in that run).

---

# Implementation Info
> A trip-planning coordinator split across `data.py` (mock travel blog posts with source metadata), `tools.py` (the three subagent-dispatch tools, their `SUBAGENT_DEFINITIONS`, and implementations), and `main.py` (system prompt + entry point), reusing the same `common/agent_loop.py` coordinator loop and `common/subagent.py` isolated-call primitive as Task 2.
## How each Task Info item is covered:
- **The Task tool / `allowedTools` requirement for a coordinator to invoke subagents** — `main.py`, `tools.py`

  ```python
  result = run_tool_loop(
      client=client, model=DEFAULT_MODEL, system=SYSTEM_PROMPT, tools=TOOLS,
      user_message=scenario, max_tokens=8192,
  )
  ```

  In Claude Code, a coordinator's `allowedTools` must list `"Task"` before it can spawn subagents; the direct analog here (raw Anthropic SDK, no Claude Code runtime) is the `tools=TOOLS` argument on the `run_tool_loop` call — the three `dispatch_*_subagent` entries in `tools.py`'s `TOOLS` list are the only surface through which the coordinator can reach a subagent at all.

- **Subagent context must be explicit — no automatic inheritance or shared memory between invocations** — `common/subagent.py`, `tools.py`

  ```python
  def run_subagent(client, model, system, user_message, max_tokens=1024) -> str:
      response = client.messages.create(
          model=model, max_tokens=max_tokens, system=system,
          messages=[{"role": "user", "content": user_message}],
      )
  ```

  `run_subagent` opens a fresh `messages=[...]` list on every call, with no reference to the coordinator's own history; `tools.py`'s three `_dispatch_*_subagent` functions show the only context each subagent ever receives is what this module explicitly builds into `user_message`.

- **`AgentDefinition` configuration (descriptions, system prompts, tool restrictions) per subagent type** — `tools.py`

  ```python
  SUBAGENT_DEFINITIONS = {
      "blog_review": {
          "description": "Extracts one structured claim+evidence finding from a single travel blog post, isolated from the rest of the trip research.",
          "system_prompt": BLOG_REVIEW_SYSTEM,
          "allowed_tools": [],
      },
      "synthesis": {...},
      "itinerary": {...},
  }
  ```

  `SUBAGENT_DEFINITIONS` gives each of the three subagent types (`blog_review`, `synthesis`, `itinerary`) an explicit `description`, `system_prompt`, and `allowed_tools` (empty for all three, since every subagent here is a single-turn, tool-free call).

- **Fork-based session management for exploring divergent approaches from a shared baseline** — `tools.py`, `main.py`

  ```python
  def _dispatch_itinerary_subagent(baseline_summary: str, style: str) -> dict:
      ...
      user_message = f"Destination summary (shared baseline):\n{baseline_summary}\n\nYour assigned style: {style}"
      itinerary = run_subagent(_client, _model, SUBAGENT_DEFINITIONS["itinerary"]["system_prompt"], user_message)
      return {"style": style, "itinerary": itinerary}
  ```

  `_dispatch_itinerary_subagent` is invoked twice with the identical `baseline_summary` text but a different `style` — the raw-API analog of Claude Code's `fork_session`, which branches a session at a shared analysis point to explore divergent approaches; verified live in the default scenario, where both the budget and luxury itineraries trace back to the same destination-summary text.

- **Passing complete findings from prior agents directly into a subagent's prompt** — `tools.py`

  ```python
  joined = "\n".join(
      f"- Claim: {f['claim']}\n"
      f"  Evidence: {f['evidence_excerpt']}\n"
      f"  Source: ({f['source']['blog_name']}, {f['source']['author']})"
      for f in findings
  )
  ```

  `_dispatch_synthesis_subagent` joins every finding's full `claim`, `evidence_excerpt`, and `source` (not just an ID or a summary) into `user_message`; the `dispatch_synthesis_subagent` tool schema requires the complete finding objects as `findings`, not references to prior `tool_use_id`s.

- **Structured data formats separating content from metadata (source, blog name, author) to preserve attribution** — `tools.py`, `data.py`

  ```python
  return {
      "post_id": post_id,
      "claim": claim,
      "evidence_excerpt": evidence,
      "source": {"blog_name": post["blog_name"], "author": post["author"]},
  }
  ```

  Every finding returned by `_dispatch_blog_review_subagent` keeps `claim`/`evidence_excerpt` (content) in separate keys from `source: {blog_name, author}` (metadata), sourced from `data.py`'s per-post metadata; the destination summary then cites each fact as `(BlogName, Author)` rather than losing attribution once content is merged — verified live in both example runs, where every claim in the summary carries its source in parentheses.

- **Spawning parallel subagents via multiple Task calls in a single coordinator response, not across separate turns** — `tools.py`, `common/agent_loop.py`

  ```python
  "once per post you need reviewed; to review several posts, emit all "
  "the calls you need together in this same turn rather than one at a "
  "time across separate turns."
  ```

  This tool description instructs emitting all needed calls "together in this same turn"; `common/agent_loop.py`'s tool-dispatch step is what makes this possible — it iterates every `tool_use` block in one `response.content` and dispatches all of them concurrently before the next API call. Verified live: the default scenario's first tool-bearing turn contains all four `dispatch_blog_review_subagent` calls (completing out of declaration order, e.g. `POST-4, POST-1, POST-3, POST-2`, since they ran concurrently), and a later single turn contains both `dispatch_itinerary_subagent` calls.

- **Coordinator prompts specifying goals/quality criteria rather than step-by-step procedure, enabling adaptability** — `main.py`

  ```python
  "Only if the user wants a specific itinerary, fork the synthesis into "
  "two divergent explorations by calling dispatch_itinerary_subagent twice ... "
  "Finish with a response addressing exactly what the user asked, no more and no less."
  ```

  The system prompt states outcomes rather than a fixed step count; verified live by the narrower "How to run" scenario, where the coordinator reviews posts and synthesizes but never calls `dispatch_itinerary_subagent`, since the user didn't ask for a specific itinerary.
