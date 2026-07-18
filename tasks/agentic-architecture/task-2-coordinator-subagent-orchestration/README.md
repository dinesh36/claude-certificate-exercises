# Task Statement 1.2: Orchestrate multi-agent systems with coordinator-subagent patterns
## Knowledge of
- Hub-and-spoke architecture where a coordinator agent manages all inter-subagent communication, error handling, and information routing
- How subagents operate with isolated context—they do not inherit the coordinator's conversation history automatically
- The role of the coordinator in task decomposition, delegation, result aggregation, and deciding which subagents to invoke based on query complexity
- Risks of overly narrow task decomposition by the coordinator, leading to incomplete coverage of broad research topics
## Skills in
- Designing coordinator agents that analyze query requirements and dynamically select which subagents to invoke rather than always routing through the full pipeline
- Partitioning research scope across subagents to minimize duplication (e.g., assigning distinct subtopics or source types to each agent)
- Implementing iterative refinement loops where the coordinator evaluates synthesis output for gaps, re-delegates to search and analysis subagents with targeted queries, and re-invokes synthesis until coverage is sufficient
- Routing all subagent communication through the coordinator for observability, consistent error handling, and controlled information flow

---

# Subject
A research coordinator helping decide whether an engineering org should stay remote-first, backed by a small tagged corpus on remote work's impact (productivity, tooling, wellbeing, security, onboarding).
- The coordinator reads the question and decides for itself which topic tags actually matter, rather than always researching all five — a narrow question gets 1-2 tags, a broad one gets full coverage.
- Each tag is researched by an isolated search subagent first at shallow depth; if the coordinator judges the gap matters, it re-dispatches the same tag with `deep_dive=true` for full coverage before synthesizing.
- One tag is deliberately flaky (simulates a subagent crash on its first call) to demonstrate that a failed tool call becomes a retryable error rather than crashing the whole run, and that it doesn't block the other topics being researched at the same time.

---

# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run tasks/agentic-architecture/task-2-coordinator-subagent-orchestration/main.py
```
Optionally pass a custom research question as the first argument:
```bash
uv run tasks/agentic-architecture/task-2-coordinator-subagent-orchestration/main.py "We're deciding whether to keep our engineering org remote-first long term. Give me a broad picture of the impact so far."
uv run tasks/agentic-architecture/task-2-coordinator-subagent-orchestration/main.py "How does going remote affect how fast new engineers ramp up?"
```
The first (broad, default) scenario makes the coordinator dispatch all 5 available topic tags, then re-dispatch every one with `deep_dive=true` after seeing `partial: true`, before running `dispatch_analysis_subagent` per tag and synthesizing. It also hits the one flaky tag (`security_risks`, see below) — its first search call raises an exception, which surfaces to the model as a retryable tool error and gets retried automatically, without disturbing the other 4 concurrently-dispatched tags. The second (narrow) scenario makes it dispatch only the 1-2 tags actually relevant to onboarding speed rather than all 5 — demonstrating query-complexity-driven subagent selection rather than a fixed pipeline.

---

# Implementation Info
> A research coordinator split across `data.py` (mock source corpus, tagged by topic), `tools.py` (the two subagent-dispatch tools and their schemas), and `main.py` (system prompt + entry point), reusing the same `common/agent_loop.py` tool-use loop from Task 1 one level up as the coordinator's own loop, plus a new shared primitive, `common/subagent.py`, for isolated single-turn subagent calls.
## How each Task Info item is covered:
- **Hub-and-spoke: coordinator manages all inter-subagent communication, error handling, and routing** — `main.py`

  ```python
  result = run_tool_loop(
      client=client,
      model=DEFAULT_MODEL,
      system=SYSTEM_PROMPT,
      tools=TOOLS,
      user_message=scenario,
  )
  ```

  The coordinator's own `run_tool_loop` call is the only place subagents are invoked from; every `dispatch_search_subagent`/`dispatch_analysis_subagent` call and result flows back through it, so no subagent ever talks to another subagent directly.

- **Subagents operate with isolated context — no automatic inheritance of the coordinator's history** — `common/subagent.py`, `tools.py`

  ```python
  def run_subagent(client, model, system, user_message, max_tokens=1024) -> str:
      response = client.messages.create(
          model=model, max_tokens=max_tokens, system=system,
          messages=[{"role": "user", "content": user_message}],
      )
      return "".join(block.text for block in response.content if block.type == "text")
  ```

  `run_subagent` opens a brand-new `messages=[...]` list and a subagent-specific `system` prompt on every call, with no reference to the coordinator's own `messages`; `tools.py`'s `_dispatch_search_subagent`/`_dispatch_analysis_subagent` show the only context a subagent ever receives is what's explicitly built into `user_message`.

- **Coordinator decomposition/delegation/aggregation and deciding which subagents to invoke based on query complexity** — `main.py`

  ```python
  "Read the user's question and decide which tags are actually relevant to "
  "it: for a narrow question, dispatch only the one or two tags that "
  "matter; for a broad question, cover enough distinct tags that no major "
  "angle is left out. Assign each subagent a single, non-overlapping tag "
  "so no two subagents research the same ground.\n\n"
  ```

  The system prompt instructs the model to read the question and choose only the relevant tags itself (not a fixed list), verified live: the broad scenario dispatches all 5 tags while the narrow onboarding-speed scenario dispatches only 1-2 (see "How to run" above).

- **Risk of overly narrow decomposition leading to incomplete coverage** — `main.py`, `tools.py`

  ```python
  "for a broad question, cover enough distinct tags that no major angle is left out."
  ```

  The prompt explicitly warns against covering too few tags on a broad question, and `tools.py`'s `dispatch_search_subagent` tool description repeats the same boundary condition at the tool level.

- **Dynamically selecting which subagents to invoke rather than always routing through the full pipeline** — `tools.py`

  ```python
  "topic_tag": {
      "type": "string",
      "enum": TOPIC_TAGS,
      "description": "The single topic to research in this call.",
  },
  ```

  `topic_tag` is an open per-call choice (not a batch parameter), so the coordinator issues exactly as many `dispatch_search_subagent` calls as it judges necessary, observed as 5 calls on the broad scenario vs. 1-2 on the narrow one.

- **Partitioning research scope across subagents to minimize duplication** — `main.py`

  ```python
  "Assign each subagent a single, non-overlapping tag "
  "so no two subagents research the same ground.\n\n"
  ```

  Enforced structurally too, since each `dispatch_search_subagent` call takes exactly one `topic_tag`.

- **Iterative refinement: evaluate synthesis for gaps, re-delegate with targeted queries, re-invoke until sufficient** — `tools.py`, `main.py`

  ```python
  result = {"topic_tag": topic_tag, "summary": summary, "partial": not deep_dive}
  if not deep_dive:
      result["gap_hint"] = (
          f"Only {len(visible)} of {len(snippets)} known sources on '{topic_tag}' were searched. "
          "Call again with deep_dive=true if this topic is central to the user's question."
      )
  ```

  Every non-`deep_dive` call returns `partial: true` plus a `gap_hint`; the system prompt instructs the coordinator to weigh each gap against the question and re-dispatch with `deep_dive=true` before finalizing, then run `dispatch_analysis_subagent` once coverage is non-partial — observed in both example runs as a first shallow pass followed by a targeted `deep_dive=true` pass on the tags that mattered.

- **Routing all subagent communication through the coordinator for observability, error handling, and controlled information flow** — `tools.py`, `common/agent_loop.py`

  ```python
  _client = get_client()
  _model = DEFAULT_MODEL

  def _dispatch_search_subagent(topic_tag: str, deep_dive: bool = False) -> dict:
      ...
      summary = run_subagent(_client, _model, SEARCH_SUBAGENT_SYSTEM, user_message)
  ```

  `tools.py`'s only export is `TOOLS` — a list of `{schema, implementation}` pairs where each `implementation` is already fully wired to a subagent call: `tools.py` builds its own client (`_client`/`_model`, module-level) rather than taking one as a parameter, so `main.py` just does `from tools import TOOLS` and hands it straight to `run_tool_loop`, identical in shape to every other task. `common/agent_loop.py` then extracts every `schema` for the Anthropic API call and builds its own name → implementation map internally to dispatch `tool_use` blocks directly — there's no separate dispatcher object anywhere in this path. As of this task that internal dispatch step is also concurrent and fault-tolerant, covered next.

## Concurrent dispatch and tool-call fault tolerance (shared infra, `common/agent_loop.py`)
A coordinator that decomposes a query into several subagent calls needs two things the original Task 1 loop didn't have to worry about (one call at a time, one dispatcher that never raised): tool calls that resolve at different speeds, and a dispatcher (an isolated Claude subagent call) that can genuinely fail. Both were added to the shared loop rather than duplicated per task, since every task reusing `run_tool_loop` benefits:
- **Concurrent execution, matched by id rather than order** — `common/agent_loop.py`

  ```python
  def _run_tool_blocks(tool_blocks, implementations, pre_hook, post_hook=None):
      with ThreadPoolExecutor(max_workers=len(tool_blocks)) as pool:
          futures = [pool.submit(_execute_tool_block, block, implementations, pre_hook, post_hook) for block in tool_blocks]
          return [future.result() for future in as_completed(futures)]
  ```

  `_run_tool_blocks` submits every `tool_use` block from a turn to a `ThreadPoolExecutor` at once and collects results via `as_completed`, so a slower subagent call never blocks a faster one; each result still carries its own `tool_use_id`, which is what the Anthropic API actually uses to match a `tool_result` back to its `tool_use` — not array position. Observed live: in the broad-scenario log the 5 `dispatch_search_subagent` calls complete in `security_risks, collaboration_tools, employee_wellbeing, onboarding_challenges, productivity` order — not declaration order — because they genuinely ran concurrently.

- **A raised exception becomes a structured, retryable error instead of crashing the run** — `common/agent_loop.py`

  ```python
  def _execute_tool_block(block, implementations, pre_hook, post_hook=None):
      try:
          blocked = pre_hook(block.name, block.input) if pre_hook else None
          if blocked is not None:
              result = blocked
          else:
              impl = implementations.get(block.name)
              result = tool_error("validation", False, f"Unknown tool '{block.name}'.") if impl is None else impl(**block.input)
      except Exception as exc:
          result = tool_error("transient", True, f"Tool '{block.name}' raised an unexpected error ({exc}) ...")
      ...
  ```

  `_execute_tool_block` wraps the `pre_hook`/implementation call in `try/except`; any exception is converted into a structured `tool_error` rather than propagating, so the run always produces a `tool_result` for every `tool_use_id` it received (the API requires exactly one) even when a subagent crashes outright.

- **Demo of the failure path** — `data.py`, `tools.py`, `main.py`

  ```python
  if topic_tag == FLAKY_TOPIC_TAG:
      attempts = _flaky_attempts.get(topic_tag, 0)
      _flaky_attempts[topic_tag] = attempts + 1
      if attempts == 0:
          raise RuntimeError(f"simulated subagent network timeout while searching '{topic_tag}'")
  ```

  `data.py`'s `FLAKY_TOPIC_TAG`/`_flaky_attempts` and this check in `tools.py` make the first `dispatch_search_subagent(topic_tag="security_risks")` call raise `RuntimeError` unconditionally (simulating a subagent-side crash, not a tool-returned error dict) — `main.py`'s system prompt instructs the coordinator to retry a transient error once, which is exactly what happens in the default broad-scenario run: the first `security_risks` call comes back as a `transient`/retryable error, the coordinator re-issues the identical call, and it succeeds.
