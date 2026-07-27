# Task Statement 3.4: Determine when to use plan mode vs direct execution
## Knowledge of
- Plan mode is designed for complex tasks involving large-scale changes, multiple valid approaches, architectural decisions, and multi-file modifications
- Direct execution is appropriate for simple, well-scoped changes (e.g., adding a single validation check to one function)
- Plan mode enables safe codebase exploration and design before committing to changes, preventing costly rework
- The Explore subagent for isolating verbose discovery output and returning summaries to preserve main conversation context
## Skills in
- Selecting plan mode for tasks with architectural implications (e.g., microservice restructuring, library migrations affecting 45+ files, choosing between integration approaches with different infrastructure requirements)
- Selecting direct execution for well-understood changes with clear scope (e.g., a single-file bug fix with a clear stack trace, adding a date validation conditional)
- Using the Explore subagent for verbose discovery phases to prevent context window exhaustion during multi-phase tasks
- Combining plan mode for investigation with direct execution for implementation (e.g., planning a library migration, then executing the planned approach)

---

# Subject
A small, real, working e-commerce checkout service (`cart.py`, `discounts.py`, `payment_processor.py`, `inventory.py`, `notifications.py`, `order_service.py`, `legacy_cart.py`, `reports.py`, plus tests). Three requests against it span a deliberate complexity gradient.
- A one-line case-sensitivity fix in `discounts.py` — simple, direct execution.
- Restructuring `order_service.py`'s synchronous checkout flow into an event-driven one — touches five files and several real architectural choices, warranting plan mode.
- Finding every reference to the deprecated `LegacyCart` class before removing it — a discovery task suited to the `Explore` subagent.

---

# How to verify
This task has no script to run — it's a small sample codebase. Open a Claude Code session with this folder as the working directory, then try the prompts below.

`.claude/settings.json` wires a `PostToolUse` hook that logs every tool call to `logs/session-behavior/task-4-plan-mode-vs-direct-execution.jsonl`. Every claim below is backed by that log.

```
Discount codes should be case-insensitive — SAVE10 and save10 should both work.
```
Expected: direct execution, no `EnterPlanMode` call. Confirmed: a single `Edit` to `discounts.py` (plus a test addition), no plan-mode tool call anywhere in the session.

```
Checkout currently blocks on payment, inventory, and email one after another in a single synchronous request. Restructure this to an async, event-driven flow: payment confirmation should publish an event that inventory reservation and the confirmation email react to independently, instead of order_service calling them all inline.
```
Expected: an `EnterPlanMode` call before any code changes — this touches five files and involves a real architectural choice (in-process event bus vs. queue vs. saga). **Environment limitation, confirmed directly:** headless `claude -p` sessions don't have `EnterPlanMode` registered at all (`ToolSearch` for `select:EnterPlanMode` returns `No matching deferred tools found`) — even a prompt that explicitly says "plan first, get my approval" produces a good written plan and correctly withholds edits, but never calls the actual tool. This bullet needs a real interactive Claude Code session to verify the tool call itself; headless mode can only confirm the reasoning, not the mechanism.

```
We want to retire LegacyCart. Find every place it's still referenced before we remove it.
```
Expected: an `Agent` call with `subagent_type: Explore`. At this codebase's actual size (9 files), a direct `Grep` sweep is fast and returns a small, clean result — a real session did exactly that, and correctly found both real references (`legacy_cart.py`'s definition, `reports.py`'s usage) with no false positives. Asked explicitly to use the Explore subagent instead, it did: a logged `Agent` call with `subagent_type: "Explore"`, which returned the same two files. Explore's actual value — isolating verbose output from the main conversation — matters most at a scale bigger than this sample codebase; both the direct-Grep and the Explore-dispatch outcomes are legitimate, scale-dependent choices.

```
Investigate the checkout service, then implement whatever the investigation turns up.
```
Expected: a plan-mode-style investigation phase, then a switch to direct execution for the implementation — the combined pattern this task statement also covers.

---

# Implementation Info
> `cart.py`/`discounts.py`/`payment_processor.py`/`inventory.py`/`notifications.py`/`order_service.py` form one small, real, tested checkout service. `legacy_cart.py` and `reports.py` add a deprecated class with two real call sites. `.claude/settings.json` and `.claude/hooks/log_tool_use.py` log every tool call a live session makes here.

## How each Task Info item is covered:
- **Plan mode is designed for complex tasks involving large-scale changes, multiple valid approaches, architectural decisions, and multi-file modifications** — `order_service.py`, `payment_processor.py`, `inventory.py`, `notifications.py`

  ```python
  # order_service.py
  """Run the full checkout flow, blocking on each step in turn.

  Every step below is a synchronous call: the payment gateway charge, the
  inventory reservation, and the confirmation email each block the request
  until they finish, one after another.
  """
  ```

  Restructuring this into an event-driven flow genuinely touches five files (`order_service.py`, `payment_processor.py`, `inventory.py`, `notifications.py`, plus a new event module) and has real competing approaches (in-process event bus, message queue, saga) — the shape of task this bullet is about.

- **Direct execution is appropriate for simple, well-scoped changes (e.g., adding a single validation check to one function)** — `discounts.py`

  ```python
  def validate_code(code: str) -> bool:
      return code in _VALID_CODES
  ```

  Making this case-insensitive is a one-function, one-file fix with an obvious implementation — confirmed live: a single `Edit` call, no plan-mode tool call anywhere in the session.

- **Plan mode enables safe codebase exploration and design before committing to changes, preventing costly rework** — hook log

  Asked to plan the checkout migration explicitly, a real session read every relevant file, laid out three named architectural options with tradeoffs, and made zero edits until asked to proceed — exploration and design before any commitment, even though the formal `EnterPlanMode` tool call itself isn't available in this headless environment (see "How to verify").

- **The Explore subagent for isolating verbose discovery output and returning summaries to preserve main conversation context** — `legacy_cart.py`, `reports.py`, hook log

  ```json
  {
    "tool_name": "Agent",
    "tool_input": { "description": "Find all LegacyCart references", "subagent_type": "Explore" }
  }
  ```

  Asked to use the Explore subagent for the `LegacyCart` search, the session dispatched an `Agent` call with `subagent_type: "Explore"` and got back a clean two-file summary, instead of the raw multi-command search output landing in the main conversation.

- **Selecting plan mode for tasks with architectural implications (e.g., microservice restructuring, library migrations affecting 45+ files, choosing between integration approaches with different infrastructure requirements)** — same checkout-migration prompt as above

  The migration prompt was deliberately built to have real competing approaches (sync fan-out vs. message queue vs. saga vs. event sourcing) rather than one obvious implementation — the exact shape this bullet names.

- **Selecting direct execution for well-understood changes with clear scope (e.g., a single-file bug fix with a clear stack trace, adding a date validation conditional)** — same case-insensitivity prompt as above

  One function, one obvious fix (`code.upper()` before the dict lookup), no competing designs to weigh — confirmed live as a single clean `Edit`.

- **Using the Explore subagent for verbose discovery phases to prevent context window exhaustion during multi-phase tasks** — same `LegacyCart` search as above

  Same hook-logged `Agent`/`Explore` call. At this sample's small scale, a direct `Grep` sweep is also legitimate and was what a real session did unprompted — Explore's benefit grows with codebase size and search verbosity, which this small sample can only partially demonstrate.

- **Combining plan mode for investigation with direct execution for implementation (e.g., planning a library migration, then executing the planned approach)** — `order_service.py` migration prompt

  A real session investigated the current architecture, proposed three named options with a recommendation, then asked for a direction before touching any code — the investigate-then-implement pattern this bullet describes, even without the formal plan-mode tool call firing in this headless environment.
