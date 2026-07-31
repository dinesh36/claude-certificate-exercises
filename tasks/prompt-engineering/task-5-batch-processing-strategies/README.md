# Task Statement 4.5: Design efficient batch processing strategies

## Knowledge of
- The Message Batches API: 50% cost savings, up to 24-hour processing window, no guaranteed latency SLA
- Batch processing is appropriate for non-blocking, latency-tolerant workloads (overnight reports, weekly audits, nightly test generation) and inappropriate for blocking workflows (pre-merge checks)
- The batch API does not support multi-turn tool calling within a single request (cannot execute tools mid-request and return results)
- custom_id fields for correlating batch request/response pairs

## Skills in
- Matching API approach to workflow latency requirements: synchronous API for blocking pre-merge checks, batch API for overnight/weekly analysis
- Calculating batch submission frequency based on SLA constraints (e.g., 4-hour windows to guarantee 30-hour SLA with 24-hour batch processing)
- Handling batch failures: resubmitting only failed documents (identified by custom_id) with appropriate modifications (e.g., chunking documents that exceeded context limits)
- Using prompt refinement on a sample set before batch-processing large volumes to maximize first-pass success rates and reduce iterative resubmission costs

---

# Subject

A legal team's weekly vendor-contract renewal-risk audit, submitted Friday evening for a Monday-morning deadline — a latency-tolerant workload that belongs on the Message Batches API. This task is scripted (the escape-hatch shape for this domain), since submitting, polling, and retrieving a batch has no chat-UI equivalent a person could exercise by typing a prompt.

- One contract's request is broken by a real sizing bug, not a staged failure — the run has to detect it by `custom_id` and resubmit just that one, with the bug fixed.
- A single urgent contract, under live negotiation on a call right now, is reviewed synchronously instead — the blocking counter-example to the batch.

---

# How to run

See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run tasks/prompt-engineering/task-5-batch-processing-strategies/main.py
```
```bash
uv run tasks/prompt-engineering/task-5-batch-processing-strategies/main.py urgent
```
The default run does the whole weekly-audit flow: a prompt-refinement sanity check, the SLA-margin and submission-interval calculations, the batch submission across all five contracts, detecting and resubmitting the one that fails, and the final merged findings. This genuinely takes a few minutes — the Batches API has no guaranteed latency SLA, and this task's own README says so before you have to discover it by waiting. The `urgent` run is the fast, synchronous contrast — seconds, not minutes, because it's a blocking call by design.

---

# Implementation Info

> `batch.py` holds the reusable Batches API mechanics (build/submit/poll/retrieve, keyed by `custom_id`). `data.py` holds the five sample contracts, the submission/deadline timestamps, and the urgent contract. `main.py` runs the prompt-refinement check, the SLA math, the weekly batch audit with its failure-and-resubmit path, and the urgent synchronous contrast.

## How each Task Info item is covered:

- **The Message Batches API: cost, window, no latency SLA** — `main.py`

  ```python
  def meets_batch_sla(hours_until_deadline: float, batch_window_hours: float = 24) -> tuple[bool, float]:
      """Whether submitting now leaves enough room for the batch's up-to-24-hour
      window, with no guaranteed latency SLA of its own — and by how much."""
      margin = hours_until_deadline - batch_window_hours
      return margin >= 0, margin
  ```
  A real run against this scenario's own timestamps (Friday 6pm submission, Monday 9am deadline) printed `63.0h available, OK (margin +39.0h over the batch window)` — the 24-hour figure is checked as a worst case, not assumed as a guarantee.

- **Batch for non-blocking workloads, sync for blocking ones** — `main.py`

  ```python
  def run_urgent_sync_review() -> None:
      """The blocking counter-example: reviewed synchronously because the
      vendor is on the phone right now, not queued into next week's batch."""
  ```
  `run_weekly_batch_audit()` and `run_urgent_sync_review()` are the two halves of this contrast — same system prompt, same model, different API entirely, chosen by whether the caller can wait. A real `urgent` run returned a full finding in seconds; the batch run took minutes.

- **The batch API can't run multi-turn tool calls mid-request** — `batch.py`

  ```python
  """Task 5: Batch Processing Strategies
  ...
  No request built here ever carries a `tools=` parameter. The Batch API
  can't pause mid-request to execute a tool and return control — a workload
  that genuinely needs multi-turn tool calling has to run through the
  synchronous API's agentic loop instead, one document at a time.
  """
  ```
  Every `Request` `build_request` constructs is a single-turn `messages.create` payload — there's no tool loop to interrupt because there's nowhere for it to resume.

- **custom_id for correlating request/response pairs** — `batch.py`

  ```python
  def collect_results(client, batch_id: str) -> tuple[dict[str, str], dict[str, str]]:
      """Splits a batch's results into (succeeded text by custom_id, failure reason by custom_id).

      Results arrive in any order — every result is matched back to its
      request by custom_id, never by position in the stream.
      """
  ```
  A real run's batch returned results in an order that didn't match submission order; every result was still matched correctly because `collect_results` keys everything by `result.custom_id`, never by position.

- **Matching API approach to latency requirements** — `main.py`

  ```python
  def main(mode: str = "batch") -> None:
      if mode == "urgent":
          run_urgent_sync_review()
          return

      run_prompt_refinement_check()
      run_weekly_batch_audit()
  ```
  The entry point itself is the decision point: `urgent` skips straight to a synchronous call, because a blocking workflow can't wait on a batch's processing window; the default path commits to the batch precisely because a weekly audit can.

- **Calculating batch submission frequency from SLA constraints** — `main.py`

  ```python
  def max_submission_interval_hours(
      sla_hours: float, batch_window_hours: float = 24, buffer_hours: float = 2
  ) -> float:
      """How often a batch must be submitted, on a recurring schedule, to
      guarantee no request waits longer than sla_hours end to end.
      ...
      Solving for the interval with the task statement's own numbers
      (30-hour SLA, 24-hour batch window, 2-hour buffer) gives 4 hours.
      """
      return sla_hours - batch_window_hours - buffer_hours
  ```
  Called with the task statement's own worked example (30h SLA, 24h batch window, 2h buffer), this returns exactly `4` — a real run printed `Worked example: a 30-hour SLA with a 24-hour batch window and a 2-hour buffer needs submissions every <= 4h.`

- **Handling batch failures: resubmitting only the failed document, with a fix** — `main.py`

  ```python
  if failed:
      print("\nResubmitting only the failed contract(s), with the sizing bug fixed:")
      retry_requests = [
          build_request(custom_id, DEFAULT_MODEL, SYSTEM_PROMPT, CONTRACTS[custom_id.removeprefix("contract-")],
                        _fixed_max_tokens_for(CONTRACTS[custom_id.removeprefix("contract-")]))
          for custom_id in failed
      ]
  ```
  A real run's first pass came back `4 succeeded, 1 failed` — `contract-titan failed: invalid_request_error: max_tokens: must be greater than or equal to 1`, caused by `_buggy_max_tokens_for`'s real bug (see below). Only `contract-titan` was resubmitted, not all five, and the corrected `_fixed_max_tokens_for` succeeded on retry.

- **Prompt refinement on a sample before committing to the full batch** — `main.py`

  ```python
  def run_prompt_refinement_check() -> None:
      """Sanity-checks the prompt on one representative contract with a plain
      synchronous call before committing the whole batch to it — cheap to fix
      now, expensive to discover after a 24-hour batch run comes back wrong."""
      sample_text = CONTRACTS["northwind"]
  ```
  This runs first, as a fast synchronous check, before `run_weekly_batch_audit()` commits five documents to a batch that might take minutes to hours to come back. This is also the module where `_buggy_max_tokens_for` and its fix live:

  ```python
  def _buggy_max_tokens_for(document_text: str) -> int:
      """Reserves 200 response tokens per paragraph break, assuming every
      contract has at least one blank-line paragraph break the intake step
      inserted. Titan's amendment is a single line with none: paragraph_count
      is 1, so (paragraph_count - 1) rounds the budget all the way to zero."""
      paragraph_count = document_text.count("\n\n") + 1
      return 200 * (paragraph_count - 1)
  ```
  Titan's one-line amendment has no paragraph breaks, so this genuinely computes `max_tokens=0` — an invalid request, not a staged one — which is exactly what a real run's batch rejected.
