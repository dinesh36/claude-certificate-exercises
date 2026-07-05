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

# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run exercises/agentic-architecture/task-1-multi-tool-agent-escalation/main.py
```
Optionally pass a custom user message as the first argument:
```bash
uv run exercises/agentic-architecture/task-1-multi-tool-agent-escalation/main.py "Can you check the status of order ORD-1004"
uv run exercises/agentic-architecture/task-1-multi-tool-agent-escalation/main.py "Can you check what kind of items CUST-1 generally orders"
uv run exercises/agentic-architecture/task-1-multi-tool-agent-escalation/main.py "Can you please refund my order - ORD-1001, it is not working"
```

---

# Implementation Info
> A customer-support agent split across `data.py` (mock order store), `tools.py` (tool schemas and implementations), `policy.py` (a programmatic refund-approval hook), and `main.py` (system prompt + entry point), with the reusable agentic loop factored out into [`common/agent_loop.py`](../../../common/agent_loop.py).
## How each Task Info item is covered:
- **Agentic loop lifecycle (send → inspect stop_reason → execute tools → return results):** [`common/agent_loop.py:75-133`](../../../common/agent_loop.py#L75-L133) — `run_tool_loop` sends the request, checks `response.stop_reason`, dispatches every `tool_use` block, and loops.
- **Loop continues on `"tool_use"`, terminates on `"end_turn"`:** [`common/agent_loop.py:107-108`](../../../common/agent_loop.py#L107-L108) — `if response.stop_reason != "tool_use": break` is the only exit condition; no iteration cap and no parsing of assistant text is used to detect completion.
- **Tool results appended to conversation history:** [`common/agent_loop.py:104`](../../../common/agent_loop.py#L104) (assistant turn) and [`common/agent_loop.py:129`](../../../common/agent_loop.py#L129) (tool_result blocks appended as the next user turn) so the model reasons over the updated context on its next call.
- **Model-driven decisions vs. pre-configured tool sequences:** [`tools.py:102-174`](./tools.py#L102-L174) — the four tool descriptions (especially `get_order_details` vs. `search_orders`, deliberately similar to test selection accuracy) and [`main.py:25-33`](./main.py#L25-L33)'s system prompt let Claude choose which tool to call and when, rather than the harness driving a fixed sequence.
- **Structured tool error responses (`errorCategory`/`isRetryable`/description):** [`common/errors.py`](../../../common/errors.py) — `tool_error(...)`, used throughout `tools.py` (e.g. [`tools.py:19-24`](./tools.py#L19-L24) validation, [`tools.py:39-44`](./tools.py#L39-L44) simulated transient failure).
- **Programmatic hook enforcing a business rule deterministically (not left to the prompt):** [`policy.py:13-27`](./policy.py#L13-L27) — `enforce_refund_policy` blocks any `process_refund` call above `REFUND_APPROVAL_THRESHOLD` before it executes; wired in via [`main.py:57`](./main.py#L57)'s `hook=enforce_refund_policy`.
- **Multi-concern decomposition and unified synthesis:** exercised by the default scenario in [`main.py:41-48`](./main.py#L41-L48), which bundles a refund request and an order lookup in one message.
- **Full transcript preserved for later inspection:** [`common/agent_loop.py:55-72`](../../../common/agent_loop.py#L55-L72) — every user/assistant/tool_result turn is appended as it happens to a per-run JSON Lines file under `logs/` at the repo root (`_log_file()`/`_append_log()`), so the complete context history survives beyond the process's own `messages` list; the resolved path is returned on [`common/agent_loop.py:41`](../../../common/agent_loop.py#L41)'s `AgentResult.log_file` and printed by [`main.py:61`](./main.py#L61).
