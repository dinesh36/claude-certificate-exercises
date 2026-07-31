# Task Statement 5.1: Manage conversation context to preserve critical information across long interactions
## Knowledge of
- Progressive summarization risks: condensing numerical values, percentages, dates, and customer-stated expectations into vague summaries
- The "lost in the middle" effect: models reliably process information at the beginning and end of long inputs but may omit findings from middle sections
- How tool results accumulate in context and consume tokens disproportionately to their relevance (e.g., 40+ fields per order lookup when only 5 are relevant)
- The importance of passing complete conversation history in subsequent API requests to maintain conversational coherence
## Skills in
- Extracting transactional facts (amounts, dates, order numbers, statuses) into a persistent "case facts" block included in each prompt, outside summarized history
- Extracting and persisting structured issue data (order IDs, amounts, statuses) into a separate context layer for multi-issue sessions
- Trimming verbose tool outputs to only relevant fields before they accumulate in context (e.g., keeping only return-relevant fields from order lookups)
- Placing key findings summaries at the beginning of aggregated inputs and organizing detailed results with explicit section headers to mitigate position effects
- Requiring subagents to include metadata (dates, source locations, methodological context) in structured outputs to support accurate downstream synthesis
- Modifying upstream agents to return structured data (key facts, citations, relevance scores) instead of verbose content and reasoning chains when downstream agents have limited context budgets

---

# Subject
A telecom support coordinator for one customer account (`CUST-48213`) who raises three separate issues — a billing dispute, a network-outage credit, and a device warranty claim — across a single long conversation.
- This task is prompt-only: `CLAUDE.md` plus three subagent instruction files drive a live Claude Code session against realistic mock account data. There's no script to run.

---

# How to verify
This task has no script to run — it's prompting artifacts and mock data. Open a Claude Code session with this folder as the working directory, then try the prompts below in order (each continues the same conversation).

`.claude/settings.json` wires a `PostToolUse` hook that logs every tool/subagent call to `logs/context-reliability/task-1-case-facts-context-preservation.jsonl`. Every claim below is backed by that log.

```
A customer contacts you about being double-billed. Investigate their billing history for the most recent invoice and tell me what happened.
```
Expected and confirmed live: an `Agent` call with `subagent_type: "billing-dispute-subagent"`, which itself `Read` only `data/billing_history.json`. The reply opened with a `## Case Facts` block holding the exact numbers verbatim — `$64.64 double-billed on invoice INV-791820`, `billed $147.36, expected $82.72`, `dispute ticket TCK-55031` — not a vague "there was a billing issue."

```
There was also a network outage last week that knocked out my data for hours, and separately my phone screen stopped working and I already filed a warranty claim. Can you check on both of those too?
```
Expected and confirmed live: two more `Agent` calls (`outage-credit-subagent`, `warranty-claim-subagent`). The reply's `## Case Facts` block kept the **original billing entry untouched** and added two new labeled entries (`**Network Outage**`, `**Warranty Claim**`) — three issues tracked at once, not just the latest. The reply also led with a `## Key Findings` summary (one line per issue) before three `### <Issue>` detail sections — key facts first, details organized under explicit headers instead of one undifferentiated block.

```
Quick question - what's my current plan and how much data have I used this cycle?
```
Expected and confirmed live: a direct `Read` of `data/customer_account.json` (56 lines, 53 fields — name, address, SIM/IMEI, loyalty points, churn-risk score, internal notes, etc.). The reply's new `**Plan & Usage**` Case Facts entry surfaced only `plan_name`, `plan_price`, `data_cap_gb`, and `data_used_gb_this_cycle` — the four fields the question needed — and the prior three issues' Case Facts entries were still present, unmodified.

---

# Implementation Info
> `CLAUDE.md` is the coordinator's system prompt, auto-loaded for any session started in this folder. `data/customer_account.json`, `data/billing_history.json`, `data/outage_log.json`, and `data/warranty_claims.json` are raw mock system records. `.claude/agents/billing-dispute-subagent.md`, `.claude/agents/outage-credit-subagent.md`, and `.claude/agents/warranty-claim-subagent.md` are real Claude Code subagents, one per issue type. `.claude/settings.json` + `.claude/hooks/log_tool_use.py` log every tool/subagent call a live session makes here.

## How each Task Info item is covered:

- **Progressive summarization risks: condensing numerical values, percentages, dates, and customer-stated expectations into vague summaries** — `CLAUDE.md`

  ```markdown
  Never compress a fact into something vague. Write `$64.64 double-billed on invoice INV-791820 (2026-06 cycle)`, not "there was a billing issue." Numbers, dates, and IDs go in verbatim — they are the one thing a summary is never allowed to blur.
  ```

  Verified live: every Case Facts entry across all three turns kept exact dollar amounts, invoice/ticket/claim IDs, and dates instead of paraphrasing them away.

- **The "lost in the middle" effect: models reliably process information at the beginning and end of long inputs but may omit findings from middle sections** — `CLAUDE.md`

  ```markdown
  1. A short `## Key Findings` summary first, one line per issue, before any detail.
  2. Full detail below it, organized under one `### <Issue name>` header per issue.

  Never bury one issue's findings in the middle of a wall of text about another issue — put headers around each so nothing in the middle gets lost.
  ```

  Verified live: the three-issue status reply put billing/outage/warranty one-liners in a `## Key Findings` block up front, then gave the outage issue (the one that would otherwise sit in the middle of the reply) its own clearly headed `### Network Outage` section — not buried between the billing and warranty detail.

- **How tool results accumulate in context and consume tokens disproportionately to their relevance (e.g., 40+ fields per order lookup when only 5 are relevant)** — `data/customer_account.json`

  ```json
  {
    "account_id": "CUST-48213",
    "customer_name": "Priya Nandakumar",
    "email": "priya.nandakumar@example.com",
    "loyalty_points": 4820,
    "churn_risk_score": "medium",
    "internal_notes": "Long-tenure customer, generally low-friction. Flagged medium churn risk after recent billing complaint on 2026-07-15."
  }
  ```

  This record has 53 fields. The plan/usage question only needed 4 of them — the exact "40+ fields when only 5 are relevant" shape the bullet describes.

- **The importance of passing complete conversation history in subsequent API requests to maintain conversational coherence** — `CLAUDE.md`

  ```markdown
  Case Facts is a supplement, not a replacement for the conversation. Keep the full turn history available in every subsequent request — don't reconstruct the conversation from the Case Facts block alone, and don't ask the customer to repeat something they already said earlier in this session.
  ```

  Verified live: the plan/usage question (turn 3) never asked the customer to re-explain the billing dispute or outage — it answered the new question while still carrying every fact from turns 1 and 2 forward in the Case Facts block.

- **Extracting transactional facts (amounts, dates, order numbers, statuses) into a persistent "case facts" block included in each prompt, outside summarized history** — `CLAUDE.md`

  ```markdown
  Every reply must open with a `## Case Facts` block, updated in place — not re-summarized from memory. It holds exact transactional facts pulled from the data files you've actually read this session: amounts, dates, invoice/ticket/claim IDs, and current status, one line per fact.
  ```

  Confirmed in every one of the three live turns — the reply always opened with `## Case Facts`, never with prose.

- **Extracting and persisting structured issue data (order IDs, amounts, statuses) into a separate context layer for multi-issue sessions** — `CLAUDE.md`

  ```markdown
  This account can have multiple open issues at once. When a new issue comes up, add a new entry to the Case Facts block — do not overwrite or drop the facts from an issue raised earlier in the same conversation. By the third issue, the block should still show all three, each labeled by issue.
  ```

  Verified live: after turn 2, the Case Facts block showed `**Billing Dispute**`, `**Network Outage**`, and `**Warranty Claim**` as three separate labeled entries — the original billing entry was untouched, not overwritten by the new issues.

- **Trimming verbose tool outputs to only relevant fields before they accumulate in context (e.g., keeping only return-relevant fields from order lookups)** — `CLAUDE.md`

  ```markdown
  For example, a billing dispute needs the disputed invoice's charge, expected amount, and dates — not `loyalty_points`, `preferred_language`, or `device_ids`.
  ```

  Verified live: turn 3's `Read` of the 53-field `customer_account.json` produced a Case Facts entry with exactly 4 fields (`plan_name`, `plan_price`, `data_cap_gb`, `data_used_gb_this_cycle`) — none of the account's name, address, loyalty, or internal-notes fields leaked into the reply.

- **Placing key findings summaries at the beginning of aggregated inputs and organizing detailed results with explicit section headers to mitigate position effects** — same turn-2 reply as above

  Already-cited turn 2 output led with `## Key Findings` (one line per issue) before the three `### <Issue>` detail sections — the exact structure this bullet describes.

- **Requiring subagents to include metadata (dates, source locations, methodological context) in structured outputs to support accurate downstream synthesis** — `.claude/agents/billing-dispute-subagent.md`, `.claude/agents/outage-credit-subagent.md`, `.claude/agents/warranty-claim-subagent.md`

  ```markdown
  BILLING FINDING
  - invoice_id: <id>
  ...
  - source: data/billing_history.json
  - record_as_of: <the file's record_as_of date>
  ```

  Verified live: every Case Facts entry produced from a subagent dispatch cited its source file and `record_as_of` date (e.g. `Source: data/outage_log.json, record as of 2026-07-30`), pulled straight from the subagent's structured return.

- **Modifying upstream agents to return structured data (key facts, citations, relevance scores) instead of verbose content and reasoning chains when downstream agents have limited context budgets** — same three subagent files

  ```markdown
  Your entire reply must be a compact structured block, not prose, not your reasoning, and never the raw file contents:
  ```

  Each subagent's instructions forbid returning prose, reasoning, or the raw file it read — only the fixed structured block. Confirmed live: the coordinator's replies folded these compact blocks straight into Case Facts rather than surfacing a subagent's raw JSON read or its internal reasoning.
