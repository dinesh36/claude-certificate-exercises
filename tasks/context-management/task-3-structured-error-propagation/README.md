# Task Statement 5.3: Implement error propagation strategies across multi-agent systems
## Knowledge of
- Structured error context (failure type, attempted query, partial results, alternative approaches) as enabling intelligent coordinator recovery decisions
- The distinction between access failures (timeouts needing retry decisions) and valid empty results (successful queries with no matches)
- Why generic error statuses ("search unavailable") hide valuable context from the coordinator
- Why silently suppressing errors (returning empty results as success) or terminating entire workflows on single failures are both anti-patterns
## Skills in
- Returning structured error context including failure type, what was attempted, partial results, and potential alternatives to enable coordinator recovery
- Distinguishing access failures from valid empty results in error reporting so the coordinator can make appropriate decisions
- Having subagents implement local recovery for transient failures and only propagate errors they cannot resolve, including what was attempted and partial results
- Structuring synthesis output with coverage annotations indicating which findings are well-supported versus which topic areas have gaps due to unavailable sources

---

# Subject
A supply-chain vendor-risk-assessment coordinator that checks one vendor (`Meridian Fabrication Co.`) against four independent data sources — a sanctions list, a news-sentiment feed, a credit bureau, and a litigation-records service.
- This task is prompt-only: `CLAUDE.md` plus four subagent instruction files drive a live Claude Code session. Each subagent calls a small, real, deterministic mock lookup script (`scripts/query_source.py`) instead of a narrated tool — no LLM is involved in deciding whether a call succeeds, times out, or is permanently down.

---

# How to verify
This task has no script to run interactively — it's prompting artifacts, mock data, and one small deterministic lookup script. Open a Claude Code session with this folder as the working directory, then try the prompts below.

`.claude/settings.json` wires a `PostToolUse` hook that logs every tool/subagent call to `logs/context-reliability/task-3-structured-error-propagation.jsonl`. It also pre-allows the one Bash command this task's subagents need (`Bash(python3 scripts/query_source.py:*)`) so a headless session doesn't stall on a permission prompt it can't answer.

**One honest caveat, confirmed directly:** in this environment, the `PostToolUse` hook does not fire for a `Bash` call whose underlying command exits non-zero (`scripts/query_source.py` exits 1 on every error response). Confirmed by running the exact same command directly, outside any subagent — a successful call logs immediately, a failing call never appears in the log at all, even though the command still ran and printed its output. This means the hook log under-counts error-path calls (see the credit-bureau and litigation-records prompts below); it doesn't mean those calls didn't happen. Three other things confirm they did:
- Running `scripts/query_source.py` directly with `python3` (no LLM at all) reproduces the exact same JSON for every mode — see the raw commands and output in the Implementation Info section.
- Claude Code's own `Agent` tool response includes a `totalToolUseCount` field independent of this task's hook — the credit-bureau subagent's response reported `"totalToolUseCount": 3` (matching attempt 1, 2, 3) even though the hook only logged one of those three Bash calls.
- The subagents' final reports include exact strings that only exist in `data/source_config.json` (e.g. the litigation alternative's precise wording) — the model can't have fabricated those.

```
Run a full vendor risk assessment for Meridian Fabrication Co. across all four sources and give me the memo.
```
Expected and confirmed live: all four subagents dispatched (`sanctions-check-subagent`, `news-sentiment-subagent`, `credit-bureau-subagent`, `litigation-records-subagent`). The final memo's `## Key Findings` listed all four sources, including the failed one, and its `## Coverage Notes` correctly sorted them into three different buckets: **well-supported** (sanctions match, credit bureau — which needed 3 attempts), **clean** (news sentiment — "no adverse coverage found", explicitly not called a gap), and **gap** (litigation records — `access_revoked`, not retryable, with the suggested manual-PACER-search alternative). The assessment never suppressed the litigation failure and never stopped early because of it.

```
Use a subagent to check the litigation-records source for Meridian Fabrication Co.
```
Expected and confirmed live: the `litigation-records-subagent` reported `status: error`, `error_type: access_revoked`, `retryable: false`, and the exact alternative from `data/source_config.json` ("manual PACER / state court docket search..."). It explicitly said this was a gap, "not a clean result" — never invented a litigation finding to fill the silence.

```
Use a subagent to check the credit-bureau source for Meridian Fabrication Co.
```
Expected and confirmed live: the `credit-bureau-subagent` reported success after 3 attempts ("took 3 attempts before succeeding") with the real credit data, and explicitly noted "no retryable failure or gap to flag" — the first two timeouts were resolved locally and never surfaced to the coordinator as errors.

---

# Implementation Info
> `CLAUDE.md` is the coordinator's system prompt, auto-loaded for any session started in this folder. `scripts/query_source.py` is a small, real, deterministic lookup tool — its behavior per source (success, valid-empty, transient-then-recovers, or permanently-down) is entirely config-driven from `data/source_config.json`, with no hidden state. `.claude/agents/*.md` are the four real Claude Code subagents, one per source. `.claude/settings.json` + `.claude/hooks/log_tool_use.py` log tool/subagent calls (see the verify section's caveat on its coverage).

## How each Task Info item is covered:

- **Structured error context (failure type, attempted query, partial results, alternative approaches) as enabling intelligent coordinator recovery decisions** — `scripts/query_source.py`, `data/source_config.json`

  ```python
  if mode == "down":
      print(json.dumps({
          "status": "error",
          "error_type": cfg.get("error_type", "access_denied"),
          "detail": cfg.get("detail", f"{args.source} is unavailable."),
          "retryable": False,
          "alternative": cfg.get("alternative"),
      }))
      sys.exit(1)
  ```

  Verified directly (`python3 scripts/query_source.py litigation_records`): `{"status": "error", "error_type": "access_revoked", "detail": "litigation-records contract lapsed on 2026-06-30; the API key was deactivated and every call now returns 401.", "retryable": false, "alternative": "manual PACER / state court docket search for the vendor's legal name and known subsidiaries"}` — failure type, what was attempted (implicit in `source`), and a concrete alternative, all in one structured object.

- **The distinction between access failures (timeouts needing retry decisions) and valid empty results (successful queries with no matches)** — `scripts/query_source.py`

  ```python
  if mode == "empty":
      print(json.dumps({"status": "success", "source": args.source, "results": []}))
      return
  ```

  `news_sentiment_feed` always returns `status: success` with an empty `results` list — never `status: error`. Verified live: the news-sentiment-subagent reported `status: success_empty` and called it "clean," never confusing it with the litigation source's genuine `status: error`.

- **Why generic error statuses ("search unavailable") hide valuable context from the coordinator** — `data/source_config.json`

  ```json
  "litigation_records": {
    "mode": "down",
    "error_type": "access_revoked",
    "detail": "litigation-records contract lapsed on 2026-06-30; the API key was deactivated and every call now returns 401.",
    "alternative": "manual PACER / state court docket search for the vendor's legal name and known subsidiaries"
  }
  ```

  Instead of a bare "search unavailable," the error carries a specific cause (contract lapsed, key deactivated, exact HTTP behavior) and a concrete next step — the coordinator's memo quoted this detail rather than a vague status.

- **Why silently suppressing errors (returning empty results as success) or terminating entire workflows on single failures are both anti-patterns** — `CLAUDE.md`

  ```markdown
  ## 1. Never treat a source error as if it were a clean result
  ...
  ## 2. Never abort the whole assessment over one source's failure
  ```

  Verified live: the full four-source run still produced a complete memo with three sources' real findings, plus the litigation gap named explicitly — never worded as "no issues found across all sources," and never refused to deliver a memo because one source failed.

- **Returning structured error context including failure type, what was attempted, partial results, and potential alternatives to enable coordinator recovery** — `.claude/agents/litigation-records-subagent.md`

  ```markdown
  Report back in this exact structured form, nothing else:

  \```
  SOURCE FINDING
  - source: litigation_records
  - status: success | success_empty | error
  - results: <one-line summary, or "none">
  - attempts_made: 1
  - error_type: <the tool's error_type>
  - retryable: false
  - alternative: <the tool's alternative field, verbatim>
  \```
  ```

  Verified live: the subagent's actual reply matched this shape exactly, including the verbatim alternative text.

- **Distinguishing access failures from valid empty results in error reporting so the coordinator can make appropriate decisions** — `.claude/agents/news-sentiment-subagent.md`

  ```markdown
  If `results` comes back as an empty list, report `status: success_empty` and say plainly that this is a clean, completed search — not a failure and not a gap in coverage.
  ```

  Verified live in the full-assessment run: the coordinator's `## Coverage Notes` placed news-sentiment under **Clean**, not **Gap** — a different bucket from litigation-records' genuine failure.

- **Having subagents implement local recovery for transient failures and only propagate errors they cannot resolve, including what was attempted and partial results** — `.claude/agents/credit-bureau-subagent.md`

  ```markdown
  If the result has `"status": "error"` and `"retryable": true`, this is a transient failure — resolve it yourself. Retry with `--attempt 2`, then `--attempt 3` if still failing. Do not tell the coordinator about a retryable error you haven't yet exhausted retries on.
  ```

  Verified live (isolated run): the credit-bureau subagent's own `Agent` tool response reported `"totalToolUseCount": 3` — three real calls (attempt 1 fail, attempt 2 fail, attempt 3 succeed) — and its final report was a clean success with `attempts_made: 3`, no error ever surfaced upstream.

- **Structuring synthesis output with coverage annotations indicating which findings are well-supported versus which topic areas have gaps due to unavailable sources** — `CLAUDE.md`

  ```markdown
  ## Coverage Notes
  - Well-supported: <sources with real results, including ones a subagent recovered on retry>
  - Clean (no adverse findings): <sources that returned a genuine empty result — this is not a gap>
  - Gap (source unavailable): <sources that errored — name the failure type and the suggested alternative>
  ```

  Verified live: the full-assessment memo's actual `Coverage Notes` sorted sanctions and credit-bureau as well-supported, news-sentiment as clean, and litigation-records as a named gap with its alternative — three distinct categories, never flattened into one undifferentiated findings list.
