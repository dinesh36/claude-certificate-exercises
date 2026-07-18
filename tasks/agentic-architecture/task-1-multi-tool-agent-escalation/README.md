# Task Statement 1.1: Design and implement agentic loops for autonomous task execution
## Knowledge of
- The agentic loop lifecycle: sending requests to Claude, inspecting stop_reason ("tool_use" vs "end_turn"), executing requested tools, and returning results for the next iteration
- How tool results are appended to conversation history so the model can reason about the next action
- The distinction between model-driven decision-making (Claude reasons about which tool to call next based on context) and pre-configured decision trees or tool sequences
## Skills in
- Implementing agentic loop control flow that continues when stop_reason is "tool_use" and terminates when stop_reason is "end_turn"
- Adding tool results to conversation context between iterations so the model can incorporate new information into its reasoning
- Avoiding anti-patterns such as parsing natural language signals to determine loop termination, setting arbitrary iteration caps as the primary stopping mechanism, or checking for assistant text content as a completion indicator

---

# Subject
A customer-support agent for an online electronics retailer that looks up orders, processes refunds, and escalates disputed cases to a human agent when they fall outside what the agent is allowed to resolve on its own.
- Answers order-status and refund questions using two similar-but-distinct lookup tools (`get_order_details` vs. `search_orders`) so the model has to pick the right one based on whether an exact order ID is known.
- Processes refunds directly, but a programmatic policy hook blocks any refund over $500 and redirects to human escalation instead of letting the model decide.
- Handles messages that bundle more than one concern (e.g. a refund request plus an unrelated order lookup) in a single reply.

---

# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run tasks/agentic-architecture/task-1-multi-tool-agent-escalation/main.py
```
Optionally pass a custom user message as the first argument:
```bash
uv run tasks/agentic-architecture/task-1-multi-tool-agent-escalation/main.py "Can you check the status of order ORD-1004"
uv run tasks/agentic-architecture/task-1-multi-tool-agent-escalation/main.py "Can you check what kind of items CUST-1 generally orders"
uv run tasks/agentic-architecture/task-1-multi-tool-agent-escalation/main.py "Can you please refund my order - ORD-1001, it is not working"
```

---

# Implementation Info
> A customer-support agent split across `data.py` (mock order store), `tools.py` (tool schemas and implementations), `policy.py` (a programmatic refund-approval hook), and `main.py` (system prompt + entry point), with the reusable agentic loop factored out into `common/agent_loop.py`.
## How each Task Info item is covered:
- **Agentic loop lifecycle (send → inspect stop_reason → execute tools → return results)** — `common/agent_loop.py`

  ```python
  while True:
      response = client.messages.create(
          model=model, max_tokens=max_tokens, system=system, tools=tools, messages=messages,
      )
      messages.append({"role": "assistant", "content": response.content})
      if response.stop_reason != "tool_use":
          break
      tool_blocks = [block for block in response.content if block.type == "tool_use"]
      tool_results = _run_tool_blocks(tool_blocks, dispatcher, pre_hook, post_hook)
      messages.append({"role": "user", "content": tool_results})
  ```

  `run_tool_loop` sends the request, checks `response.stop_reason`, dispatches every `tool_use` block, and loops.

- **Loop continues on `"tool_use"`, terminates on `"end_turn"`** — `common/agent_loop.py`

  ```python
  if response.stop_reason != "tool_use":
      break
  ```

  The only exit condition in the whole loop; no iteration cap and no parsing of assistant text is used to detect completion.

- **Tool results appended to conversation history** — `common/agent_loop.py`

  ```python
  messages.append({"role": "assistant", "content": response.content})
  ...
  messages.append({"role": "user", "content": tool_results})
  ```

  The assistant's turn (including its `tool_use` blocks) is appended first, then the dispatched `tool_result` blocks are appended as the next user turn, so the model reasons over the updated context on its next call.

- **Model-driven decisions vs. pre-configured tool sequences** — `tools.py`, `main.py`

  ```python
  "name": "get_order_details",
  "description": (
      "Fetch full details for a SINGLE order when you already have its exact order ID "
      "... Do NOT use this to browse or search — if you don't have an exact order "
      "ID yet, use search_orders instead."
  ),
  ...
  "name": "search_orders",
  "description": (
      "Look up a customer's orders when you do NOT have an exact order ID ... "
      "Do NOT use this if an exact order ID is already known; call get_order_details instead."
  ),
  ```

  The four tool descriptions (especially `get_order_details` vs. `search_orders`, deliberately similar to test selection accuracy) plus `main.py`'s system prompt let Claude choose which tool to call and when, rather than the harness driving a fixed sequence.

- **Structured tool error responses (`errorCategory`/`isRetryable`/description)** — `common/errors.py`, `tools.py`

  ```python
  def tool_error(error_category: ErrorCategory, is_retryable: bool, description: str) -> dict:
      return {"errorCategory": error_category, "isRetryable": is_retryable, "description": description}
  ```

  Used throughout `tools.py`, e.g. `tool_error("validation", False, "No order found with ID ...")` and `tool_error("transient", True, "Order search service timed out. Retry the request.")`.

- **Programmatic hook enforcing a business rule deterministically (not left to the prompt)** — `policy.py`, `main.py`

  ```python
  def enforce_refund_policy(tool_name: str, tool_input: dict) -> dict | None:
      if tool_name != "process_refund":
          return None
      amount = tool_input.get("amount")
      if isinstance(amount, (int, float)) and amount > REFUND_APPROVAL_THRESHOLD:
          return tool_error("permission", False, f"Refund amount {amount} exceeds the ${REFUND_APPROVAL_THRESHOLD:.2f} threshold ...")
      return None
  ```

  `enforce_refund_policy` blocks any `process_refund` call above `REFUND_APPROVAL_THRESHOLD` before it executes; wired in via `main.py`'s `pre_hook=enforce_refund_policy`.

- **Multi-concern decomposition and unified synthesis** — `main.py`

  ```python
  "Hi, I have two things. First, order ORD-1003 arrived defective and I want a full "
  "refund. Second, can you check what else customer CUST-2 has ordered recently?"
  ```

  The default scenario bundles a refund request and an order lookup in one message, exercised by the system prompt's "decompose multi-part requests into distinct concerns" instruction.

- **Full transcript preserved for later inspection** — `common/agent_loop.py`

  ```python
  def _append_log(record: dict) -> None:
      path = _log_file()
      path.parent.mkdir(parents=True, exist_ok=True)
      record = {"timestamp": datetime.now(timezone.utc).isoformat(), **record}
      with path.open("a", encoding="utf-8") as f:
          f.write(json.dumps(_to_jsonable(record)) + "\n")
  ```

  Every user/assistant/tool_result turn is appended as it happens to a per-run JSON Lines file under `logs/` at the repo root, so the complete context history survives beyond the process's own `messages` list; the resolved path is returned on `AgentResult.log_file` and printed by `main.py`.
