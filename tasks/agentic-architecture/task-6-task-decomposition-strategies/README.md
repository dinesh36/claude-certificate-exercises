# Task Statement 1.6: Design task decomposition strategies for complex workflows
## Knowledge of
- When to use fixed sequential pipelines (prompt chaining) versus dynamic adaptive decomposition based on intermediate findings
- Prompt chaining patterns that break reviews into sequential steps (e.g., analyze each file individually, then run a cross-file integration pass)
- The value of adaptive investigation plans that generate subtasks based on what is discovered at each step
## Skills in
- Selecting task decomposition patterns appropriate to the workflow: prompt chaining for predictable multi-aspect reviews, dynamic decomposition for open-ended investigation tasks
- Splitting large code reviews into per-file local analysis passes plus a separate cross-file integration pass to avoid attention dilution
- Decomposing open-ended tasks (e.g., "add comprehensive tests to a legacy codebase") by first mapping structure, identifying high-impact areas, then creating a prioritized plan that adapts as dependencies are discovered

---

# Subject
A manufacturing quality-control coordinator that picks its decomposition strategy to fit the request rather than always following the same script.
- Naming specific batch IDs triggers a FIXED pipeline: one `inspect_batch` call per named batch, then a single `run_cross_batch_defect_trend` integration pass over all of them together.
- Describing an open-ended customer-reported product defect (no batch IDs) triggers a DYNAMIC path instead: `scope_customer_defect_report` runs first, and only the root-cause areas it actually flags get a follow-up `investigate_root_cause` call. The number of follow-ups genuinely varies per product — one area for PRODUCT-A, two for PRODUCT-B — rather than being scripted.

---

# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run tasks/agentic-architecture/task-6-task-decomposition-strategies/main.py
```
Optionally pass a custom user message as the first argument:
```bash
uv run tasks/agentic-architecture/task-6-task-decomposition-strategies/main.py "Can you review production batches BATCH-101, BATCH-102, and BATCH-103 from today's runs and tell me if there's a pattern?"
uv run tasks/agentic-architecture/task-6-task-decomposition-strategies/main.py "A customer returned a batch of PRODUCT-A units with cracking near the left edge. Can you find out why?"
uv run tasks/agentic-architecture/task-6-task-decomposition-strategies/main.py "We're getting reports of inconsistent wall thickness on PRODUCT-B. Please investigate."
```
- **First (default) scenario:** names three batch IDs, so the agent runs the fixed pipeline — one `inspect_batch` call per batch, then one `run_cross_batch_defect_trend` pass that surfaces the evening-shift defect concentration.
- **Second scenario:** describes an open-ended PRODUCT-A defect with no batch IDs. The agent scopes first, finds only one flagged area (`materials`), and produces exactly one `investigate_root_cause` follow-up.
- **Third scenario:** does the same for PRODUCT-B, whose scope flags two areas (`calibration`, `process_step`), producing two follow-up calls. This proves the dynamic path's fan-out is decided at runtime by what the scope discovers, not fixed in the prompt.

---

# Implementation Info
> A quality-control coordinator split across `data.py` (mock batch and defect-report data), `tools.py` (the four tool schemas/implementations for both decomposition patterns), and `main.py` (system prompt + entry point), reusing `common/agent_loop.py`'s tool-use loop unchanged — no hooks needed for this task.
## How each Task Info item is covered:
- **When to use fixed sequential pipelines (prompt chaining) versus dynamic adaptive decomposition based on intermediate findings** — `main.py`

  ```python
  "If the user names specific batch IDs to review, use the FIXED "
  "pipeline: call inspect_batch once per named batch, emitting all of "
  "those calls together in this same turn, then once you have every "
  "batch's findings, call run_cross_batch_defect_trend with the complete "
  "findings to look for a cross-batch pattern.\n\n"
  "If the user describes an open-ended customer-reported defect on a "
  "product (no batch IDs given), use the DYNAMIC path instead: call "
  "scope_customer_defect_report first to see which root-cause areas "
  "actually look suspicious, then call investigate_root_cause only for "
  "the areas that came back flagged"
  ```

  The system prompt makes the choice explicit and mutually exclusive — named batch IDs route to the fixed pipeline, an open-ended product complaint routes to the dynamic path, never both for the same request.

- **Prompt chaining patterns that break reviews into sequential steps (e.g., analyze each file individually, then run a cross-file integration pass)** — `tools.py`

  ```python
  def _inspect_batch(batch_id: str) -> dict:
      batch = BATCHES.get(batch_id)
      if batch is None:
          return tool_error("validation", False, f"No batch found with ID '{batch_id}'.")
      return {"batch_id": batch_id, **batch}


  def _run_cross_batch_defect_trend(findings: list[dict]) -> dict:
      ...
      by_shift: dict[str, list[int]] = {}
      for f in findings:
          by_shift.setdefault(f["shift"], []).append(f["defect_count"])
      shift_averages = {shift: sum(counts) / len(counts) for shift, counts in by_shift.items()}
  ```

  `_inspect_batch` is the per-item local analysis pass — one call per batch, no cross-batch awareness. `_run_cross_batch_defect_trend` is the separate integration pass that only runs once every batch has been inspected. Together they mirror the per-file-then-cross-file review pattern.

- **The value of adaptive investigation plans that generate subtasks based on what is discovered at each step** — `data.py`

  ```python
  DEFECT_REPORTS = {
      "PRODUCT-A": {
          "reported_issue": "Cracking near the left edge on a batch of returned units.",
          "flagged_areas": {
              "materials": "Raw material lot #M-2291 tested below spec tensile strength for this run.",
          },
      },
      "PRODUCT-B": {
          "reported_issue": "Inconsistent wall thickness reported by a customer.",
          "flagged_areas": {
              "calibration": "Extrusion die sensor drifted 0.4mm out of calibration mid-shift.",
              "process_step": "Cooling stage residence time was reduced during a line-speed change.",
          },
      },
  }
  ```

  PRODUCT-A's scope flags a single area, while PRODUCT-B's flags two. The set of follow-up `investigate_root_cause` subtasks is generated from what the scope step actually discovers per product — not a fixed count baked into the prompt.

- **Selecting task decomposition patterns appropriate to the workflow: prompt chaining for predictable multi-aspect reviews, dynamic decomposition for open-ended investigation tasks** — `main.py`

  ```python
  "Do not blend the two "
  "patterns for a single request; pick the one that fits, then write a "
  "unified conclusion."
  ```

  The prompt forces a single, deliberate pattern choice per request rather than letting the model default to one pattern regardless of fit.

- **Splitting large code reviews into per-file local analysis passes plus a separate cross-file integration pass to avoid attention dilution** — `tools.py`

  ```python
  "description": (
      "Analyze the COMPLETE prior inspect_batch results together for a cross-batch "
      "pattern (e.g. a shift correlation). Pass every finding explicitly — this tool "
      "has no access to prior inspect_batch results on its own. Use this once you've "
      "inspected every batch the user named; this is the integration pass that closes "
      "out the fixed pipeline."
  ),
  ```

  `run_cross_batch_defect_trend` deliberately has no memory of prior calls, and requires every finding to be passed explicitly. The per-batch inspection and the cross-batch trend analysis stay two distinct passes, instead of one call trying to do both at once — the same reasoning behind per-file-then-cross-file code review.

- **Decomposing open-ended tasks (e.g., "add comprehensive tests to a legacy codebase") by first mapping structure, identifying high-impact areas, then creating a prioritized plan that adapts as dependencies are discovered** — `tools.py`

  ```python
  def _scope_customer_defect_report(product_id: str) -> dict:
      report = DEFECT_REPORTS.get(product_id)
      if report is None:
          return tool_error("validation", False, f"No defect report found for product '{product_id}'.")

      return {
          "product_id": product_id,
          "reported_issue": report["reported_issue"],
          "areas_checked": ROOT_CAUSE_AREAS,
          "areas_flagged": list(report["flagged_areas"]),
      }
  ```

  `scope_customer_defect_report` maps the full space of possible root-cause areas first (`areas_checked`), then narrows to only the ones worth a deeper look (`areas_flagged`). This is the same map-then-prioritize shape as scoping a legacy codebase before deciding where testing effort actually pays off.

  `investigate_root_cause` refuses to run on an area the scope didn't flag (see `tools.py`'s validation branch), so the plan only ever adapts to what was genuinely discovered.
