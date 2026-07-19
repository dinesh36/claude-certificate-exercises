# Task Statement 1.4: Implement multi-step workflows with enforcement and handoff patterns
## Knowledge of
- The difference between programmatic enforcement (hooks, prerequisite gates) and prompt-based guidance for workflow ordering
- When deterministic compliance is required (e.g., identity verification before financial operations), prompt instructions alone have a non-zero failure rate
- Structured handoff protocols for mid-process escalation that include customer details, root cause analysis, and recommended actions
## Skills in
- Implementing programmatic prerequisites that block downstream tool calls until prerequisite steps have completed (e.g., blocking process_refund until get_customer has returned a verified customer ID)
- Decomposing multi-concern customer requests into distinct items, then investigating each in parallel using shared context before synthesizing a unified resolution
- Compiling structured handoff summaries (customer ID, root cause, refund amount, recommended action) when escalating to human agents who lack access to the conversation transcript

---

# Subject
An IT helpdesk agent handling employee requests for system access, where granting access is gated behind manager sign-off and some systems can never be auto-granted at all.
- `grant_access` is blocked by a policy hook until `verify_manager_approval` has actually confirmed approval for that exact employee and system — not just because the model was told to check first.
- Certain systems are "restricted-tier" and always require a human security-team sign-off, even when manager approval is already on file.
- Handles requests that bundle an access request with an unrelated question (e.g. "grant me access, and also tell me what I already have") in one reply, and escalates with a structured handoff (employee ID, root cause, recommended action) whenever the gate blocks the request.

---

# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run tasks/agentic-architecture/task-4-multi-step-enforcement-handoff/main.py
```
Optionally pass a custom user message as the first argument:
```bash
uv run tasks/agentic-architecture/task-4-multi-step-enforcement-handoff/main.py "Hi, I'm Alex Kim (EMP-1). I need access to the shared-drive system, and separately, can you tell me what access I currently have?"
uv run tasks/agentic-architecture/task-4-multi-step-enforcement-handoff/main.py "Hi, I'm Jamie Lopez (EMP-2). I need access to Salesforce."
uv run tasks/agentic-architecture/task-4-multi-step-enforcement-handoff/main.py "Hi, I'm Alex Kim (EMP-1). I need access to prod-admin."
```
- **First (default) scenario:** manager approval is already on file for a standard-tier system. `verify_manager_approval` confirms it, `grant_access` succeeds, and the unrelated `check_access_level` lookup runs in the same reply.
- **Second scenario:** no approval is on file. `verify_manager_approval` reports `approved: false`, and the agent escalates without ever calling `grant_access`.
- **Third scenario:** approval is on file, but for a restricted-tier system. `grant_access` is blocked by the policy hook regardless, and the agent escalates — proving the tier check is enforced even when the prerequisite was otherwise satisfied.

---

# Implementation Info
> An IT-helpdesk agent split across `data.py` (mock employee/approval records), `tools.py` (tool schemas, implementations, and the `verified_approvals` record), `policy.py` (the prerequisite-gate hook), and `main.py` (system prompt + entry point), reusing `common/agent_loop.py`'s tool-use loop.
## How each Task Info item is covered:
- **Programmatic enforcement (hooks, prerequisite gates) vs. prompt-based guidance** — `policy.py`, `main.py`

  ```python
  def enforce_access_prerequisite(tool_name: str, tool_input: dict) -> dict | None:
      if tool_name != "grant_access":
          return None
      ...
      if (employee_id, system) not in verified_approvals:
          return tool_error("permission", False, f"grant_access is blocked: verify_manager_approval has not confirmed approval for ...")
      return None
  ```

  The system prompt also *asks* the model to verify before granting, but `enforce_access_prerequisite` is the actual gate. Passed to `run_tool_loop` as `pre_hook=enforce_access_prerequisite` in `main.py`, it runs before every tool call and can block `grant_access` outright — regardless of what the prompt says, or whether the model follows it.

- **Deterministic compliance where prompt instructions alone have non-zero failure rate** — `policy.py`, `tools.py`

  ```python
  if SYSTEM_TIERS.get(system) == "restricted":
      return tool_error("permission", False, f"'{system}' is a restricted-tier system — it always requires human security-team sign-off ...")
  ```

  Restricted-tier systems are blocked unconditionally by the hook. Verified live: even when `verify_manager_approval` reports `approved: true` for a restricted system (`prod-admin`), `grant_access` is still blocked. This rule is enforced in code against `SYSTEM_TIERS` — it isn't left to the model to remember or infer from the prompt.

- **Structured handoff protocols (customer/employee details, root cause, recommended action)** — `tools.py`

  ```python
  def _escalate_to_security_team(employee_id, issue_summary, root_cause, recommended_action, system="") -> dict:
      ticket_id = f"SEC-{abs(hash((employee_id, issue_summary))) % 100000:05d}"
      return {
          "ticket_id": ticket_id, "employee_id": employee_id, "system": system or None,
          "issue_summary": issue_summary, "root_cause": root_cause,
          "recommended_action": recommended_action, "status": "escalated_to_security_team",
      }
  ```

  Every escalation carries the employee ID, a root-cause explanation, and a recommended action. Verified live in both escalation scenarios: the agent filled in a specific root cause (e.g. "no manager approval on file" vs. "restricted-tier system"), not a generic failure message.

- **Programmatic prerequisites blocking a downstream tool call until a prior step has completed** — `tools.py`, `policy.py`

  ```python
  verified_approvals: set[tuple[str, str]] = set()

  def _verify_manager_approval(employee_id: str, system: str) -> dict:
      ...
      approved = APPROVALS.get((employee_id, system), False)
      if approved:
          verified_approvals.add((employee_id, system))
  ```

  `grant_access` is only ever unblocked once `verify_manager_approval` has actually run and recorded the `(employee_id, system)` pair in `verified_approvals`. This is the direct analog of "blocking process_refund until get_customer has returned a verified customer ID" — a real record of what happened, not something the model's tool-call ordering could fake.

- **Decomposing multi-concern requests and investigating each in parallel before a unified synthesis** — `main.py`

  ```python
  "Decompose multi-part requests into distinct concerns and address each one. "
  ```

  Verified live in the default scenario: the access request and the unrelated "what do I currently have" question are dispatched as `verify_manager_approval` and `check_access_level` in the same turn. They run concurrently, per `common/agent_loop.py`, then get resolved together in one final reply.

- **Structured handoff summaries when escalating to humans who lack the conversation transcript** — `tools.py`, `policy.py`

  ```python
  "Hand off the request to a human security-team member. Use this when grant_access is "
  "blocked by policy (no approval on file, or a restricted-tier system) ..."
  ```

  The `escalate_to_security_team` tool description ties escalation directly to the two ways `policy.py`'s hook can block `grant_access`. The handoff summary's `root_cause` field can always name the specific policy reason, instead of a vague "couldn't complete this."
