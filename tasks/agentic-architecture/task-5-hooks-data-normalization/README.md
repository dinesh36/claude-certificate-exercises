# Task Statement 1.5: Apply Agent SDK hooks for tool call interception and data normalization
## Knowledge of
- Hook patterns (e.g., PostToolUse) that intercept tool results for transformation before the model processes them
- Hook patterns that intercept outgoing tool calls to enforce compliance rules (e.g., blocking refunds above a threshold)
- The distinction between using hooks for deterministic guarantees versus relying on prompt instructions for probabilistic compliance
## Skills in
- Implementing PostToolUse hooks to normalize heterogeneous data formats (Unix timestamps, ISO 8601, numeric status codes) from different MCP tools before the agent processes them
- Implementing tool call interception hooks that block policy-violating actions (e.g., refunds exceeding $500) and redirect to alternative workflows (e.g., human escalation)
- Choosing hooks over prompt-based enforcement when business rules require guaranteed compliance

---

# Subject
A shipment-tracking desk that checks package status across three mock carrier systems and can issue shipping credits for delivery problems.
- Each carrier tool returns delivery status in a different raw shape: Unix epoch + numeric code, ISO 8601 + free-text status, or a custom date string + single-letter flag. A PostToolUse hook rewrites every one of them into one consistent shape before the model ever sees it.
- `issue_shipping_credit` is blocked by a separate PreToolUse hook above a $75 threshold, redirecting to a human claims-desk escalation with a structured handoff instead of leaving the limit to the prompt.

---

# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run tasks/agentic-architecture/task-5-hooks-data-normalization/main.py
```
Optionally pass a custom user message as the first argument:
```bash
uv run tasks/agentic-architecture/task-5-hooks-data-normalization/main.py "Can you check on my two packages, FDX-1001 and RC-2002?"
uv run tasks/agentic-architecture/task-5-hooks-data-normalization/main.py "My package RC-2002 was delayed. Can you issue a \$50 credit for the inconvenience?"
uv run tasks/agentic-architecture/task-5-hooks-data-normalization/main.py "My package LG-3003 had an issue. Please issue a \$150 credit."
```
- **First (default) scenario:** checks a FedEx-style package and a regional-courier package in one turn. Both raw formats (Unix epoch + numeric code, and ISO 8601 + free-text status) come back normalized into the same shape.
- **Second scenario:** requests a credit under the $75 threshold, which is issued directly.
- **Third scenario:** requests a $150 credit. The policy hook blocks it regardless of the package's legacy-carrier date format, and the agent escalates instead of retrying.

---

# Implementation Info
> A shipment-tracking desk split across `data.py` (mock per-carrier records), `tools.py` (tool schemas and implementations), `normalize.py` (the PostToolUse normalization hook), `policy.py` (the PreToolUse credit-threshold hook), and `main.py` (system prompt + entry point), reusing `common/agent_loop.py`'s tool-use loop — extended this task with a `post_hook` parameter alongside its existing `pre_hook`.
## How each Task Info item is covered:
- **Hook patterns (e.g., PostToolUse) that intercept tool results for transformation before the model processes them** — `common/agent_loop.py`, `normalize.py`

  ```python
  result = dispatcher(block.name, block.input)
  if post_hook and not is_tool_error(result):
      result = post_hook(block.name, block.input, result)
  ```

  `_execute_tool_block` runs `post_hook` on every successful dispatch result, before it's ever turned into a `tool_result` block. `main.py` wires `normalize.py`'s `normalize_carrier_result` in as `post_hook=normalize_carrier_result`.

- **Hook patterns that intercept outgoing tool calls to enforce compliance rules (e.g., blocking refunds above a threshold)** — `common/agent_loop.py`, `policy.py`

  ```python
  blocked = pre_hook(block.name, block.input) if pre_hook else None
  if blocked is not None:
      result = blocked
  else:
      result = dispatcher(block.name, block.input)
  ```

  `pre_hook` runs before the dispatcher and can short-circuit the call entirely. `policy.py`'s `enforce_credit_threshold` uses this to block `issue_shipping_credit` above `CREDIT_APPROVAL_THRESHOLD`, before it ever executes.

- **The distinction between hooks for deterministic guarantees vs. prompt instructions for probabilistic compliance** — `main.py`, `policy.py`

  ```python
  "credits above the policy threshold are automatically blocked and redirected to escalation; if "
  "that happens, do not retry issue_shipping_credit, escalate to escalate_to_claims_desk instead."
  ```

  The prompt *asks* the model to respect the threshold and stop retrying once blocked. `enforce_credit_threshold` is what actually guarantees it. Verified live: the $150 request was blocked by the hook regardless of what the model intended, and the model never got a chance to bypass it by retrying.

- **PostToolUse hooks normalizing heterogeneous data formats (Unix timestamps, ISO 8601, numeric status codes) from different tools** — `normalize.py`

  ```python
  if tool_name == "check_fedex_status":
      last_update = datetime.fromtimestamp(result["epoch_ts"], tz=timezone.utc).isoformat()
      status = FEDEX_STATUS_CODES.get(result["code"], "unknown")
  elif tool_name == "check_regional_courier_status":
      last_update = result["timestamp"]
      status = REGIONAL_STATUS_MAP.get(result["status"], result["status"].lower().replace(" ", "_"))
  else:  # check_legacy_carrier_status
      parsed = datetime.strptime(result["date_str"], "%m-%d-%Y %I:%M %p").replace(tzinfo=timezone.utc)
  ```

  Three genuinely different raw shapes all collapse into one `{tracking_id, carrier, status, last_update}` shape:
  - Unix epoch + numeric code
  - ISO 8601 + free-text status
  - A custom `MM-DD-YYYY HH:MM AM/PM` string + single-letter flag

  Verified live in the default scenario: the FedEx and regional-courier results both came back with an identical field structure and status vocabulary.

- **Tool call interception hooks blocking policy-violating actions and redirecting to alternative workflows (e.g. human escalation)** — `policy.py`, `tools.py`

  ```python
  return tool_error(
      "permission", False,
      f"Credit amount {amount} exceeds the ${CREDIT_APPROVAL_THRESHOLD:.2f} threshold "
      "a human claims-desk agent must approve. Blocked by policy hook — escalate to "
      "escalate_to_claims_desk instead of retrying issue_shipping_credit.",
  )
  ```

  The blocked error explicitly names the alternative workflow (`escalate_to_claims_desk`). Verified live: after the $150 credit was blocked, the agent called `escalate_to_claims_desk` with a structured summary, instead of retrying `issue_shipping_credit`.

- **Choosing hooks over prompt-based enforcement when business rules require guaranteed compliance** — `common/agent_loop.py`

  ```python
  """Two hook points bracket every tool call (Domain 1.5): `pre_hook` runs before
  dispatch and can block it outright (PreToolUse-style — deterministic policy
  enforcement, e.g. refusing a call above a threshold); `post_hook` runs after
  a successful dispatch and can transform the result before the model ever
  sees it (PostToolUse-style — e.g. normalizing heterogeneous timestamp/status
  formats from different tools into one shape)."""
  ```

  Both hook points are enforced in code (`common/agent_loop.py`), not left to the system prompt. The module docstring states why this exists as a shared, reusable primitive rather than a task-specific prompt convention: business rules that must hold every time belong in a hook, not a request to the model.
