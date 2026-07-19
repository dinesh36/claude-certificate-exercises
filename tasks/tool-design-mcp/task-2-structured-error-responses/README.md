# Task Statement 2.2: Implement structured error responses for MCP tools
## Knowledge of
- The MCP isError flag pattern for communicating tool failures back to the agent
- The distinction between transient errors (timeouts, service unavailability), validation errors (invalid input), business errors (policy violations), and permission errors
- Why uniform error responses (generic "Operation failed") prevent the agent from making appropriate recovery decisions
- The difference between retryable and non-retryable errors, and how returning structured metadata prevents wasted retry attempts
## Skills in
- Returning structured error metadata including errorCategory (transient/validation/permission), isRetryable boolean, and human-readable descriptions
- Including retriable: false flags and customer-friendly explanations for business rule violations so the agent can communicate appropriately
- Implementing local error recovery within subagents for transient failures, propagating to the coordinator only errors that cannot be resolved locally along with partial results and what was attempted
- Distinguishing between access failures (needing retry decisions) and valid empty results (representing successful queries with no matches)

---

# Subject
A warehouse-fulfillment MCP server whose four tools deliberately exercise every error category the task statement covers, instead of ever returning a generic "Operation failed" string.
- `reserve_stock` and `search_inventory` return validation errors (bad input, and a business-rule violation — requesting more stock than exists — mapped to the same `validation` category with a customer-friendly description).
- `ship_order` returns a permission error when an order above the approval threshold has no authorized manager attached.
- `check_carrier_status` distinguishes a locally-recoverable transient failure (one carrier region down, retried internally, folded into a partial result) from a genuinely unrecoverable one (every region down, raised as a retryable transient error).
- `search_inventory` also demonstrates the companion distinction: a query that matches nothing is a normal, successful empty result, not an error — only a genuinely invalid (blank) query raises.

---

# How to connect and run
This task is a real MCP server, not a script you `uv run` directly — Claude Code is the client that talks to it.

1. **Register the server** (run from inside this task folder, so it's scoped to just this task rather than every project on your machine):
   ```bash
   cd tasks/tool-design-mcp/task-2-structured-error-responses
   claude mcp add --transport stdio warehouse-fulfillment -- uv run --directory "$(pwd)" server.py
   ```
   This uses the default **local** scope, stored in `~/.claude.json` keyed to this exact directory. It won't appear in any other project, and won't touch this repo's own root `.mcp.json`.

   The `--directory "$(pwd)"` bakes the absolute task-folder path into the registered command itself. Without it, the stored command is the bare relative `uv run server.py`, which only resolves when Claude Code happens to spawn it with this folder as the process's cwd. `claude mcp list` would then report `✘ Failed to connect` from anywhere else — even though the registration itself is fine.
2. **Verify it connected:**
   ```bash
   claude mcp list
   ```
   `warehouse-fulfillment` should show as `✔ Connected`.
3. **Start a Claude Code session from this same directory** and try these prompts — each is designed to exercise one error-handling decision the task statement is about:
   ```
   Search the warehouse inventory for 'drone'.
   ```
   Should return an empty match list, not an error — verified live: the agent correctly reported "no matches" rather than treating the lookup as failed.
   ```
   Reserve 999 units of SKU-1042 for a big order.
   ```
   Should return a non-retryable validation error naming the actual stock level. Verified live: the agent explained this is "a non-retryable validation error — retrying with the same quantity won't help" and suggested reducing the quantity or waiting for restock.
   ```
   Ship ORDER-501 with approval from RANDOM-EMPLOYEE.
   ```
   Should return a non-retryable permission error. Verified live: the agent identified it as "a `permission` error, non-retryable" and asked for a valid manager ID instead of retrying.
   ```
   Check the carrier status for ORDER-777.
   ```
   Should return a partial success — most regions fine, one unresolved. Verified live: the agent reported region-east and region-central as in transit, and region-west as "unresolved after 3 local retries," without treating the whole call as failed.
   ```
   Check the carrier status for ORDER-999.
   ```
   Should return a retryable transient error (every region unresolved). Verified live: the agent flagged it as "retryable (`isRetryable: true`)... worth trying again shortly rather than treating it as a permanent failure."
4. **Leave the server registered.** Once verified, keep it attached rather than removing it. If you edit `server.py` later, re-attach it (`claude mcp remove warehouse-fulfillment` then the `claude mcp add` command above again) so a new session spawns the updated code.

---

# Implementation Info
> `server.py` creates the FastMCP instance and defines all four tools, each wrapped in `common/mcp_logging.py`'s `logged_tool` decorator and raising `common/errors.py`'s `StructuredToolError` on failure paths; `data.py` holds the mock inventory/order/carrier data.
## How each Task Info item is covered:
- **The MCP isError flag pattern for communicating tool failures back to the agent** — `common/errors.py`

  ```python
  class StructuredToolError(Exception):
      """Raise from an MCP tool implementation to surface a `tool_error()` dict
      through FastMCP's isError mechanism, instead of a bare failure string.

      FastMCP turns any raised exception into an isError=true tool result whose
      content is the exception's string — this exception's string is the
      JSON-serialized error dict, so the agent can parse errorCategory/
      isRetryable/description back out of it rather than getting only free text.
      """

      def __init__(self, error_category: ErrorCategory, is_retryable: bool, description: str):
          super().__init__(json.dumps(tool_error(error_category, is_retryable, description)))
  ```

  Raising `StructuredToolError` is what makes FastMCP set `isError: true` — the exception's message is JSON, not free text, so the flag and the structured payload arrive together.

- **The distinction between transient errors, validation errors, business errors (policy violations), and permission errors** — `server.py`

  ```python
  raise StructuredToolError("validation", False, "quantity must be a positive integer.")
  ...
  raise StructuredToolError("permission", False, f"Order {order_id} is ${order['value_usd']:.2f}, ...")
  ...
  raise StructuredToolError("transient", True, "All carrier regions are unreachable after local retries; safe to retry this call.")
  ```

  Three of the four category names appear as literal, distinct raise sites across the server's tools: `validation` in `search_inventory`/`reserve_stock`/unknown-ID checks, `permission` in `ship_order`, and `transient` in `check_carrier_status`. A business-rule violation (requesting more stock than exists) also raises `validation` — see the next bullet for why there's no separate `"business"` literal.

- **Why uniform error responses (generic "Operation failed") prevent the agent from making appropriate recovery decisions** — verified live, `README.md`

  The five live prompts above produced five *different* agent reactions:
  - "No matches" (not a failure)
  - "Non-retryable, reduce the quantity"
  - "Non-retryable, need a real manager ID"
  - "Partial success, one region down"
  - "Retryable, try again shortly"

  None of these would have been possible from a single generic `"Operation failed"` string. The structured `errorCategory`/`isRetryable` fields are what let the agent choose a different next action for each one, instead of reacting identically to all of them.

- **The difference between retryable and non-retryable errors, and how returning structured metadata prevents wasted retry attempts** — `server.py`

  ```python
  if not results:
      raise StructuredToolError(
          "transient",
          True,
          "All carrier regions are unreachable after local retries; safe to retry this call.",
      )
  ```

  `check_carrier_status`'s all-regions-down case is the only `isRetryable: True` raise in the server. Every validation/permission raise is `False`, since retrying an unknown SKU or an unapproved manager ID with the exact same arguments can never succeed.

  Verified live: the agent used exactly this distinction, recommending a retry only for the transient case and explicitly saying "retrying... won't help" for the validation and permission cases.

- **Returning structured error metadata including errorCategory (transient/validation/permission), isRetryable boolean, and human-readable descriptions** — `common/errors.py`

  ```python
  def tool_error(error_category: ErrorCategory, is_retryable: bool, description: str) -> dict:
      return {
          "errorCategory": error_category,
          "isRetryable": is_retryable,
          "description": description,
      }
  ```

  `StructuredToolError` builds its message from this exact dict shape — every one of this server's raised errors carries all three fields, not just a description.

- **Including retriable: false flags and customer-friendly explanations for business rule violations so the agent can communicate appropriately** — `server.py`

  ```python
  raise StructuredToolError(
      "validation",
      False,
      f"Only {item['stock']} unit(s) of '{item['name']}' ({sku}) are in stock right now — "
      f"you requested {quantity}. Reduce the quantity or check back after the next restock.",
  )
  ```

  `reserve_stock`'s insufficient-stock case is `isRetryable: False` with a description written for a human to read directly ("Reduce the quantity or check back after the next restock"), not a technical exception trace.

  Verified live: the agent relayed this near verbatim rather than paraphrasing it into something more technical.

- **Implementing local error recovery within subagents for transient failures, propagating to the coordinator only errors that cannot be resolved locally along with partial results and what was attempted** — `server.py`

  ```python
  for region in CARRIER_REGIONS:
      if region in flaky_regions:
          unresolved.append(f"{region}: retried 3x locally, still unreachable (simulated timeout)")
      else:
          results[region] = f"in transit via {region}"
  ...
  return {"order_id": order_id, "results": results, "partial": bool(unresolved), "unresolved": unresolved}
  ```

  `check_carrier_status` retries each region locally and only surfaces the ones that never recovered. It returns a normal, successful `partial` result carrying both what succeeded and exactly what was attempted for what didn't, rather than failing the whole call over one bad region. Only when literally nothing recovered does it escalate to a raised (transient, retryable) error.

- **Distinguishing between access failures (needing retry decisions) and valid empty results (representing successful queries with no matches)** — `server.py`

  ```python
  if not query.strip():
      raise StructuredToolError("validation", False, "query must not be empty.")

  query_lower = query.lower()
  matches = [...]
  return {"query": query, "matches": matches, "count": len(matches)}
  ```

  A blank query is a genuine validation failure (raised). A well-formed query that simply matches nothing returns normally with an empty `matches` list and `count: 0`.

  Verified live: searching for "drone" (no such product) was reported as "no matches," never as an error the agent felt it should retry or escalate.
