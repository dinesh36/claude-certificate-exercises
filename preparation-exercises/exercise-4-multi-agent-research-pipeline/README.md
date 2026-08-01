# Preparation Exercise 4: Design and Debug a Multi-Agent Research Pipeline

**Objective:** Practice orchestrating subagents, managing context passing, implementing error propagation, and handling synthesis with provenance tracking.

**Steps:**
1. Build a coordinator agent that delegates to at least two subagents (e.g., web search and document analysis). Ensure the coordinator's allowedTools includes "Task" and that each subagent receives its research findings directly in its prompt rather than relying on automatic context inheritance.
2. Implement parallel subagent execution by having the coordinator emit multiple Task tool calls in a single response. Measure the latency improvement compared to sequential execution.
3. Design structured output for subagents that separates content from metadata: each finding should include a claim, evidence excerpt, source URL/document name, and publication date. Verify that the synthesis subagent preserves source attribution when combining findings.
4. Implement error propagation: simulate a subagent timeout and verify the coordinator receives structured error context (failure type, attempted query, partial results). Test that the coordinator can proceed with partial results and annotate the final output with coverage gaps.
5. Test with conflicting source data (e.g., two credible sources with different statistics) and verify the synthesis output preserves both values with source attribution rather than arbitrarily selecting one, and structures the report to distinguish well-established from contested findings.

---

# Subject

A research coordinator studying renewable-energy adoption rates across four regions (California, Texas, Germany, Japan), dispatching two independent subagent sources per region: an industry analyst report and a government statistics bulletin.

- One region's government data feed is deliberately, persistently down (not a one-time flake) — the coordinator has to proceed with partial results instead of retrying forever.
- One region's two sources genuinely disagree on the adoption figure — the synthesis has to preserve both, not pick one.

---

# How to run / verify

See the repository root [README](../../README.md) for one-time setup (`uv` project, `ANTHROPIC_API_KEY`).

```bash
uv run preparation-exercises/exercise-4-multi-agent-research-pipeline/main.py
```

Every run first prints a standalone concurrent-vs-sequential latency measurement (Step 2), independent of the live coordinator call, then runs the default scenario: all 4 regions, both sources each.

```bash
uv run preparation-exercises/exercise-4-multi-agent-research-pipeline/main.py "What's the wind adoption rate in Texas, from both the industry report and government data?"
```
A single region — isolates the conflicting-source path (Texas: 28% industry vs. 24% government) without the full 4-region breadth.

```bash
uv run preparation-exercises/exercise-4-multi-agent-research-pipeline/main.py "What's the renewable adoption rate in Germany?"
```
Isolates the coverage-gap path: the industry report succeeds, the government feed fails every attempt.

**Verification status:** the Anthropic API key backing this environment is currently out of credit, so the coordinator's own tool-selection and synthesis behavior hasn't been driven through a live run yet. What *has* been verified directly, without needing the API: the latency measurement above (a real `0.51s` concurrent vs. `4.03s` sequential for 8 simulated calls, an 8.0x speedup — not an estimate); that Germany's government-data dispatch returns the identical structured `transient` error on repeated calls, not a one-time flake; and that an unknown region returns a `validation` error from both dispatch tools. Re-run the scenarios above once credits are available to confirm the coordinator's actual behavior, rather than trusting this note as a substitute.

---

# Implementation Info

> `tools.py` holds the two subagent-dispatch tools and their `TOOLS` export. `data.py` holds the mock report/bulletin sources, including Texas's conflicting figures and Germany's always-down feed. `main.py` is the system prompt, the entry point, and the standalone latency-measurement helper. All three reuse `common/agent_loop.py`'s coordinator loop and `common/subagent.py`'s isolated-call primitive, the same as `tasks/agentic-architecture/task-2` and `task-3`.

## How each Step is covered:

- **Step 1 — Build a coordinator that delegates to at least two subagents; allowedTools includes "Task"; each subagent receives its findings directly in its prompt rather than automatic context inheritance** — `tools.py`, `common/subagent.py`

  ```python
  def run_subagent(client: Anthropic, model: str, system: str, user_message: str, max_tokens: int = 1024) -> str:
      """Run one isolated, tool-free subagent turn and return its text output."""
      response = client.messages.create(
          model=model, max_tokens=max_tokens, system=system,
          messages=[{"role": "user", "content": user_message}],
      )
  ```

  This task uses the raw Anthropic SDK rather than the Claude Code runtime, so the direct analog of `allowedTools` including `"Task"` is the `tools=TOOLS` argument on `main.py`'s `run_tool_loop` call — `dispatch_industry_report_subagent` and `dispatch_government_data_subagent` are the only surface through which the coordinator can reach a subagent. `run_subagent` opens a fresh `messages=[...]` list every call, with no reference to the coordinator's own history — each dispatch function builds `user_message` from only the one report/bulletin excerpt it was given.

- **Step 2 — Parallel subagent execution via multiple Task calls in a single response; measure the latency improvement over sequential execution** — `main.py`

  ```python
  def measure_dispatch_latency(call_count: int) -> tuple[float, float]:
      start = time.monotonic()
      with ThreadPoolExecutor(max_workers=call_count) as pool:
          futures = [pool.submit(_simulate_subagent_call) for _ in range(call_count)]
          for future in as_completed(futures):
              future.result()
      concurrent_seconds = time.monotonic() - start
      ...
  ```

  `common/agent_loop.py`'s own tool dispatch already runs every `tool_use` block in a turn concurrently via `ThreadPoolExecutor` — the same mechanism `task-2`/`task-3` rely on. This exercise adds a real, measured comparison on top of that: `measure_dispatch_latency` times 8 simulated subagent calls (the default scenario's 4 regions × 2 sources) both concurrently and sequentially, using the same `SIMULATED_SUBAGENT_LATENCY_SECONDS` sleep `tools.py`'s real dispatch implementations use. Verified directly: `0.51s` concurrent vs. `4.03s` sequential — an `8.0x` speedup, not an estimate.

- **Step 3 — Structured output separating content from metadata (claim, evidence excerpt, source URL/document name, publication date); synthesis preserves source attribution** — `tools.py`

  ```python
  return {
      "region": region,
      "claim": report["claim"],
      "evidence_excerpt": report["evidence_excerpt"],
      "subagent_summary": summary,
      "source": {"name": report["source_name"], "url": report["source_url"]},
      "publication_date": report["publication_date"],
  }
  ```

  Every finding keeps `claim`/`evidence_excerpt` (content) separate from `source`/`publication_date` (metadata) — the exact four fields Step 3 names. The system prompt instructs the coordinator to "preserve all of these when you report back, never just a bare number," so attribution survives into the final synthesis rather than being dropped once the numbers are combined.

- **Step 4 — Error propagation: simulate a subagent timeout, verify structured error context (failure type, attempted query, partial results); coordinator proceeds with partial results and annotates coverage gaps** — `tools.py`, `data.py`

  ```python
  if record is None:
      return tool_error(
          "transient",
          True,
          (
              f"Timeout querying the government statistics feed. Failure type: "
              f"connection_timeout. Attempted query: region='{region}', "
              "dataset='renewable_adoption_rate'. This feed has been unavailable across "
              "repeated attempts for this region — if a retry also fails, proceed with only "
              "the industry-report finding for this region and note the coverage gap rather "
              "than retrying indefinitely."
          ),
      )
  ```

  Germany's government-data dispatch always returns this same structured error — verified directly across two consecutive calls, identical both times, unlike a one-time flake that would succeed on retry. The description carries the failure type (`connection_timeout`) and the attempted query (`region`, `dataset`) Step 4 asks for. The system prompt tells the coordinator to retry once, then proceed with only the industry-report finding and note the gap — not retry indefinitely or invent a number.

- **Step 5 — Conflicting source data: synthesis preserves both values with attribution rather than arbitrarily selecting one; report distinguishes well-established from contested findings** — `data.py`, `main.py`

  ```python
  # tools.py, texas industry report:
  "claim": "Wind adoption in Texas reached 28% of grid generation in the latest reporting period.",
  # tools.py, texas government data:
  "claim": "Texas state filing reports wind at 24% of grid generation for the latest period.",
  ```

  Texas's two sources genuinely disagree (28% vs. 24%) for the same claim, while California, Germany, and Japan's available sources corroborate each other. The system prompt instructs: "When two sources report different figures for the same region, report the discrepancy explicitly — both numbers, both sources — do not average them, and do not silently pick one," and to structure the final report into "Well-established findings" vs. "Contested findings" sections, plus a "Coverage gaps" note — exactly the three-way split Step 5 (together with Step 4) asks for.
