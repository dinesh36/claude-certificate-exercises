# Task Statement 5.2: Design effective escalation and ambiguity resolution patterns

## Knowledge of
- Appropriate escalation triggers: customer requests for a human, policy exceptions/gaps (not just complex cases), and inability to make meaningful progress
- The distinction between escalating immediately when a customer explicitly demands it versus offering to resolve when the issue is straightforward
- Why sentiment-based escalation and self-reported confidence scores are unreliable proxies for actual case complexity
- How multiple customer matches require clarification (requesting additional identifiers) rather than heuristic selection

## Skills in
- Adding explicit escalation criteria with few-shot examples to the system prompt demonstrating when to escalate versus resolve autonomously
- Honoring explicit customer requests for human agents immediately without first attempting investigation
- Acknowledging frustration while offering resolution when the issue is within the agent's capability, escalating only if the customer reiterates their preference
- Escalating when policy is ambiguous or silent on the customer's specific request (e.g., competitor price matching when policy only addresses own-site adjustments)
- Instructing the agent to ask for additional identifiers when tool results return multiple matches, rather than selecting based on heuristics

---

# Subject

A support desk for Waypoint Stays, a hotel booking platform, handling guest requests about reservations, duplicate charges, and cancellations.

- This task is prompt-only: every Skills-in bullet is exercised by a system prompt plus documented prompts fired at a live Claude Code session in this folder, not by a script.

---

# How to verify

This task has no script to run — it's prompting artifacts and mock data. Open a Claude Code session with this folder as the working directory. Start by telling Claude to adopt the persona in [system-prompt.md](system-prompt.md) for the rest of the conversation, then send the prompts below one at a time (a fresh session per prompt isolates each case cleanly, but a single session works too since none of the cases depend on each other).

`.claude/settings.json` wires a `PostToolUse` hook that logs every tool call to `logs/context-reliability/task-2-escalation-ambiguity-resolution.jsonl`. Every claim below is backed by that log.

```
I don't want to explain my whole situation again, just put me through to a person.
```
Expected: the agent escalates immediately, with **no** `Read`/`Grep` tool call logged beforehand — it never attempts to look up a reservation first.

```
I've called THREE TIMES about this — I was charged twice for my stay under confirmation HTL-10399 and nobody has fixed it!!
```
Expected: the log shows a `Read`/`Grep` call against `data/reservations.md`, confirming the duplicate $410 charge on HTL-10399. The agent acknowledges the frustration in its reply but resolves the refund itself rather than escalating, since a confirmed duplicate charge is within its stated capability.

```
There's a hurricane warning near my destination next week — can I cancel my reservation for a full refund even though it's inside the normal cancellation window?
```
Expected: the agent reads `policy.md`, finds no exception for weather events (only the documented medical-emergency exception), and escalates rather than approving or denying the refund itself.

```
Hi, I need to change my checkout date. My name is Alex Turner.
```
Expected: the log shows a lookup against `data/reservations.md` returning two matches (HTL-10234 and HTL-10567, both "Alex Turner"). The agent asks for the confirmation number or check-in date instead of picking one.

```
Can you send me a receipt for my last stay? My name is Priya Nair.
```
Expected: a single, unambiguous match (HTL-10842). The agent resolves this directly without escalating — the contrast case showing the system prompt's few-shot examples correctly route a straightforward, in-capability request to autonomous resolution rather than escalation.

---

# Implementation Info

> `system-prompt.md` is the agent's persona and escalation policy; `policy.md` and `data/reservations.md` are the records it looks up mid-conversation; `.claude/hooks/log_tool_use.py` turns "the agent looked this up before answering" into a checkable log entry instead of a claim.

## How each Task Info item is covered:

- Escalation criteria + few-shot examples in the system prompt — `system-prompt.md`

  ```markdown
  ## Escalation criteria

  Escalate to a human agent (say so plainly, and stop resolving the issue yourself) in exactly these cases:

  1. **The guest explicitly asks for a human.** Escalate immediately. Do not look anything up first, do not ask a clarifying question first, do not try to resolve the issue first — an explicit request for a human is not a data-gathering step.
  2. **The policy doesn't address the guest's specific situation.** If `policy.md` is silent or ambiguous about the exact case in front of you, don't guess which way it would probably go. Escalate and say why.
  3. **You cannot make meaningful progress** — e.g. no reservation exists under any identifier the guest can provide.
  ```

  The four few-shot examples further down the same file each pair a guest message with the correct agent behavior, so the escalation criteria aren't just stated abstractly — they're demonstrated.

- Honoring explicit human requests without investigating first — `system-prompt.md`

  ```markdown
  **Example 1 — explicit human request, escalate immediately:**
  > Guest: "I don't want to explain my whole situation again, just put me through to a person."
  > Agent: "Of course — connecting you with a human agent now so you don't have to repeat anything." *(no lookup attempted first)*
  ```

  Verified live by the first prompt in "How to verify": the hook log shows no `Read`/`Grep` call before the escalation reply.

- Acknowledging frustration while resolving in-capability issues, escalating only on reiteration — `system-prompt.md`

  ```markdown
  Do **not** escalate just because:
  - The guest sounds upset or frustrated. Acknowledge the frustration, then resolve the issue yourself if it's within your capability (documented below). Only escalate if the guest reiterates that they want a human after you've offered to help.
  ```

  Verified live by the duplicate-charge prompt: the agent looks up HTL-10399 in `data/reservations.md`, confirms the frustration is warranted, and resolves the refund itself instead of escalating on sentiment alone.

- Escalating when policy is silent on the specific request — `policy.md`

  ```markdown
  No other exceptions to the standard window are defined in this policy. Situations not listed here (for example, weather events, flight disruptions, or other travel changes outside the guest's control) are not addressed — do not assume they are covered by the medical-emergency exception, and do not assume they are automatically denied either.
  ```

  Verified live by the hurricane prompt: the agent reads this file, finds no matching exception, and escalates instead of guessing either direction.

- Asking for additional identifiers on multiple matches instead of guessing — `data/reservations.md` + `system-prompt.md`

  ```markdown
  | HTL-10234    | Alex Turner | 2026-08-10 | 2026-08-14 | Deluxe King   | Confirmed | —  |
  | HTL-10567    | Alex Turner | 2026-09-02 | 2026-09-05 | Standard Queen| Confirmed | —  |
  ```

  Two records share the guest name "Alex Turner" on purpose. `system-prompt.md`'s "Multiple matches" section instructs the agent to ask for a confirmation number or check-in date rather than pick one heuristically — verified live by the Alex Turner prompt, and contrasted by the single-match Priya Nair prompt, which resolves directly.
