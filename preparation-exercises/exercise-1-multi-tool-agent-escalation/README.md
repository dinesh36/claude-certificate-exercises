# Preparation Exercise 1: Build a Multi-Tool Agent with Escalation Logic

> **Objective:** Practice designing an agentic loop with tool integration, structured error handling, and escalation patterns.
> **Domains reinforced:** [Domain 1](../../wiki/tasks/1-agentic-architecture) (Agentic Architecture & Orchestration), [Domain 2](../../wiki/tasks/2-tool-design-mcp) (Tool Design & MCP Integration), [Domain 5](../../wiki/tasks/5-context-management) (Context Management & Reliability)

Source: [`wiki/tasks/6-preparation-exercises.md`](../../wiki/tasks/6-preparation-exercises.md), Exercise 1.

---

# Subject

A release-engineering agent for a software company's deployment pipeline. It checks deployment status, lists a service's deployments, requests new deploys, and escalates high-risk production deploys to the on-call lead instead of auto-approving them.

- Every step is coded into one agentic-loop script (`main.py`/`tools.py`/`policy.py`/`data.py`) — no prompt-only steps.

---

# How to run

See the repository root [README](../../README.md) for one-time setup (`uv` project, `ANTHROPIC_API_KEY`).

```bash
uv run preparation-exercises/exercise-1-multi-tool-agent-escalation/main.py
```

Default scenario: a high-risk production deploy request (blocked by the policy hook, then escalated to the on-call lead) plus a staging deployment lookup (fails transient once, then succeeds on retry) — both concerns resolved in one turn.

```bash
uv run preparation-exercises/exercise-1-multi-tool-agent-escalation/main.py "What's the current status of deployment DEPLOY-2005?"
```

A direct-ID lookup — exercises `get_deployment_status` vs. `list_deployments` disambiguation on the happy path.

```bash
uv run preparation-exercises/exercise-1-multi-tool-agent-escalation/main.py "Deploy version 1.0.0 of billing-service to production with a risk score of 4."
```

A validation error: `billing-service` isn't a known service, so the agent explains the error instead of retrying.

---

# Implementation Info

> `main.py` is the entry point and system prompt. `tools.py` holds the four tool schemas/implementations. `policy.py` is the pre-dispatch hook enforcing the production risk threshold. `data.py` is the mock deployment store.

## How each Step is covered:

- **Step 1 — Define 3-4 tools with detailed descriptions that clearly differentiate purpose, inputs, and boundary conditions; include at least two similar tools that require careful disambiguation** — `tools.py`

  ```python
  "name": "get_deployment_status",
  "description": (
      "Fetch full status for a SINGLE deployment when you already have its exact "
      "deployment ID (format 'DEPLOY-XXXX') ... Do NOT use this to browse or search — if you "
      "don't have an exact deployment ID yet, use list_deployments instead."
  ),
  ...
  "name": "list_deployments",
  "description": (
      "Look up a service's deployments when you do NOT have an exact deployment ID ... "
      "Do NOT use this if an exact deployment ID is already known; call get_deployment_status instead."
  ),
  ```

  `get_deployment_status` and `list_deployments` are a deliberately similar pair (both return deployment info) — verified live: "What's the current status of deployment DEPLOY-2005?" correctly picks `get_deployment_status`, never `list_deployments`.

- **Step 2 — Implement an agentic loop that checks `stop_reason` to continue or present the final response, handling both `"tool_use"` and `"end_turn"`** — [`common/agent_loop.py`](../../common/agent_loop.py)

  ```python
  response = client.messages.create(**create_kwargs)
  messages.append({"role": "assistant", "content": response.content})
  ...
  if response.stop_reason != "tool_use":
      break
  tool_blocks = [block for block in response.content if block.type == "tool_use"]
  tool_results = _run_tool_blocks(tool_blocks, tool_implementations, pre_hook, post_hook)
  messages.append({"role": "user", "content": tool_results})
  ```

  `main.py` never implements this loop itself — it calls `run_tool_loop(...)`, which is this exact loop, terminating strictly on `stop_reason` rather than an iteration cap or parsed text.

- **Step 3 — Add structured error responses (`errorCategory`, `isRetryable`, human-readable description); verify the agent retries transient errors and explains business errors** — `tools.py`, `data.py`

  ```python
  attempts = _list_attempts.get(service, 0)
  _list_attempts[service] = attempts + 1
  if attempts == 0:
      return tool_error(
          "transient",
          True,
          "Deployment inventory service timed out. Retry the request.",
      )
  ```

  Verified live: the default scenario's `list_deployments("checkout-api", "staging")` call fails transient on the first attempt and the agent retries automatically, succeeding on the second call — while the "billing-service" scenario's `validation` error (unknown service) is explained to the user with no retry attempted.

- **Step 4 — Implement a programmatic hook that intercepts tool calls to enforce a business rule (e.g. blocking operations above a threshold), redirecting to an escalation workflow** — `policy.py`

  ```python
  def enforce_deploy_risk_policy(tool_name: str, tool_input: dict) -> dict | None:
      if tool_name != "request_deploy":
          return None
      if tool_input.get("environment") != "production":
          return None
      risk_score = tool_input.get("risk_score")
      if isinstance(risk_score, (int, float)) and risk_score > PRODUCTION_RISK_THRESHOLD:
          return tool_error("permission", False, f"Risk score {risk_score} exceeds the production threshold of {PRODUCTION_RISK_THRESHOLD}. ...")
      return None
  ```

  Verified live: requesting a production deploy of `payments-service` at risk score 9 (threshold is 7) is blocked before the tool implementation ever runs, and the agent calls `escalate_to_oncall` with a structured handoff (ticket ID, root cause, recommended action) instead of retrying `request_deploy`.

- **Step 5 — Test with multi-concern messages and verify the agent decomposes the request, handles each concern, and synthesizes a unified response** — `main.py`

  ```python
  "Please deploy version 4.2.0 of payments-service to production with a risk score "
  "of 9. Also, can you check what deployments checkout-api currently has running in "
  "staging?"
  ```

  Verified live: one turn resolves both concerns — the blocked/escalated production deploy and the retried-then-successful staging lookup — and the final response addresses each separately before summarizing.

## Domain 5 note

Domain 5 (Context Management & Reliability) is reinforced via the full transcript logging `common/agent_loop.py` performs for every run (`logs/*.jsonl`) — the conversation history and every tool result stay recoverable after the process ends, independent of which scenario above is run.
