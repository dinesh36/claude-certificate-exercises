# Preparation Task 1: Build a Multi-Tool Agent with Escalation Logic

> **Objective:** Practice designing an agentic loop with tool integration, structured error handling, and escalation patterns.
> **Domains reinforced:** [Domain 1](../../../wiki/tasks/1-agentic-architecture) (Agentic Architecture & Orchestration), [Domain 2](../../../wiki/tasks/2-tool-design-mcp) (Tool Design & MCP Integration), [Domain 5](../../../wiki/tasks/5-context-management) (Context Management & Reliability)

Source: [`wiki/tasks/6-preparation-tasks.md`](../../../wiki/tasks/6-preparation-tasks.md), Task 1.

---

## Status: Fully covered

Every step below is already exercised by an existing, verified task — no new implementation needed.

## How each step is covered

- **Step 1 — Define 3–4 tools with detailed descriptions that clearly differentiate purpose, inputs, and boundary conditions; include at least two similar tools that require careful disambiguation** — [`tasks/agentic-architecture/task-1-multi-tool-agent-escalation`](../../agentic-architecture/task-1-multi-tool-agent-escalation/README.md)

  That task's own tool set is 4 tools, including a deliberately similar pair:
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

  For the MCP-protocol-specific angle (a real MCP server, not just SDK tool schemas) on the exact same disambiguation problem, see [`tasks/tool-design-mcp/task-1-tool-interface-clarity-boundaries`](../../tool-design-mcp/task-1-tool-interface-clarity-boundaries/README.md), which splits an ambiguous `get_item(id)` into `fetch_user_story`/`fetch_bug_ticket`.

- **Step 2 — Implement an agentic loop that checks `stop_reason` to continue or present the final response, handling both `"tool_use"` and `"end_turn"`** — [`tasks/agentic-architecture/task-1-multi-tool-agent-escalation`](../../agentic-architecture/task-1-multi-tool-agent-escalation/README.md) (`common/agent_loop.py`)

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

- **Step 3 — Add structured error responses (`errorCategory`, `isRetryable`, human-readable description); verify the agent retries transient errors and explains business errors** — [`tasks/agentic-architecture/task-1-multi-tool-agent-escalation`](../../agentic-architecture/task-1-multi-tool-agent-escalation/README.md) (`common/errors.py`)

  ```python
  def tool_error(error_category: ErrorCategory, is_retryable: bool, description: str) -> dict:
      return {"errorCategory": error_category, "isRetryable": is_retryable, "description": description}
  ```

  For a fuller, dedicated treatment of every error category (transient, validation, permission) with live-verified agent reactions to each, see [`tasks/tool-design-mcp/task-2-structured-error-responses`](../../tool-design-mcp/task-2-structured-error-responses/README.md).

- **Step 4 — Implement a programmatic hook that intercepts tool calls to enforce a business rule (e.g. blocking operations above a threshold), redirecting to an escalation workflow** — [`tasks/agentic-architecture/task-1-multi-tool-agent-escalation`](../../agentic-architecture/task-1-multi-tool-agent-escalation/README.md) (`policy.py`)

  ```python
  def enforce_refund_policy(tool_name: str, tool_input: dict) -> dict | None:
      if tool_name != "process_refund":
          return None
      amount = tool_input.get("amount")
      if isinstance(amount, (int, float)) and amount > REFUND_APPROVAL_THRESHOLD:
          return tool_error("permission", False, f"Refund amount {amount} exceeds the ${REFUND_APPROVAL_THRESHOLD:.2f} threshold ...")
      return None
  ```

- **Step 5 — Test with multi-concern messages and verify the agent decomposes the request, handles each concern, and synthesizes a unified response** — [`tasks/agentic-architecture/task-1-multi-tool-agent-escalation`](../../agentic-architecture/task-1-multi-tool-agent-escalation/README.md) (`main.py`)

  ```python
  "Hi, I have two things. First, order ORD-1003 arrived defective and I want a full "
  "refund. Second, can you check what else customer CUST-2 has ordered recently?"
  ```

## Domain 5 note

The preparation task lists Domain 5 (Context Management & Reliability) as reinforced, via the full transcript logging `common/agent_loop.py` performs for every run (`logs/*.jsonl`) — the conversation history and every tool result stay recoverable after the process ends, which is the reliability/context-preservation angle this step touches. No dedicated Domain 5 task exists in this repo yet (see the [preparation-tasks index](../README.md)).
