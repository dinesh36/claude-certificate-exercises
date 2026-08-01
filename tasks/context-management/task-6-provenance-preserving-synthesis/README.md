# Task Statement 5.6: Preserve information provenance and handle uncertainty in multisource synthesis
## Knowledge of
- How source attribution is lost during summarization steps when findings are compressed without preserving claim-source mappings
- The importance of structured claim-source mappings that the synthesis agent must preserve and merge when combining findings
- How to handle conflicting statistics from credible sources: annotating conflicts with source attribution rather than arbitrarily selecting one value
- Temporal data: requiring publication/collection dates in structured outputs to prevent temporal differences from being misinterpreted as contradictions
## Skills in
- Requiring subagents to output structured claim-source mappings (source URLs, document names, relevant excerpts) that downstream agents preserve through synthesis
- Structuring reports with explicit sections distinguishing well-established findings from contested ones, preserving original source characterizations and methodological context
- Completing document analysis with conflicting values included and explicitly annotated, letting the coordinator decide how to reconcile before passing to synthesis
- Requiring subagents to include publication or data collection dates in structured outputs to enable correct temporal interpretation
- Rendering different content types appropriately in synthesis outputs—financial data as tables, news as prose, technical findings as structured lists—rather than converting everything to a uniform format

---

# Subject
A market-research coordinator synthesizes EV-adoption findings for California in 2025 from three sources: an industry analyst report, a news article, and a government vehicle-registration dataset.
- This task is prompt-only: `CLAUDE.md` plus three subagent instruction files drive a live Claude Code session over three mock source documents. There's no script to run.
- The three sources are built to genuinely conflict (three different California EV-share figures for the same period, using three different methodologies) and to include a temporal look-alike (a mid-year figure that could be mistaken for disagreeing with the full-year figures if dates weren't tracked).

---

# How to verify
This task has no script to run — it's prompting artifacts and three mock source documents. Open a Claude Code session with this folder as the working directory, then try the prompts below.

`.claude/settings.json` wires a `PostToolUse` hook that logs every tool/subagent call to `logs/context-reliability/task-6-provenance-preserving-synthesis.jsonl`. Every claim below is backed by that log — all three subagent dispatches and their underlying `Read` calls were captured cleanly.

```
Synthesize what all three sources say about EV adoption in California in 2025, and give me the full report.
```
Expected and confirmed live: all three subagents dispatched (`analyst-report-subagent`, `news-article-subagent`, `gov-dataset-subagent`), each returning a list of structured `CLAIM` blocks (claim, value, source name, URL, published date, data period, methodology, verbatim excerpt) — never prose summaries.

The final report came back with exactly the three sections `CLAUDE.md` calls for:
- **Well-Established Findings** — the CA DOT's registration counts (1,742,300 total; 543,600 EV) and YoY change, reported as an uncontested structured list, attributed to "California DOT" throughout.
- **Contested Findings** — a comparison table of California's full-year 2025 EV share: GreenDrive Analytics' 38.4% (sales-based estimate), The Daily Circuit's "close to 35%" (analysts' estimate), and CA DOT's 31.2% (registration-based). The report explicitly called this "a genuine conflict, not a rounding difference" and refused to pick a winner — it named the methodology difference (sales estimates vs. registration counts) as the likely explanation instead of collapsing the three into one number.
- **Temporally Distinct (not a conflict)** — The Daily Circuit's mid-year "roughly 30%, as of June 2025" figure was correctly separated from the full-year figures above it, with an explicit note that a mid-year and a full-year number aren't in tension.

Source attribution was preserved throughout: every figure in the report is stated as "GreenDrive Analytics reports..." / "CA DOT's dataset shows..." / "The Daily Circuit... according to dealership groups," never as a bare number.

---

# Implementation Info
> `CLAUDE.md` is the coordinator's system prompt, auto-loaded for any session started in this folder. `data/analyst_report.md`, `data/news_article.md`, and `data/gov_transportation_dataset.md` are the three mock sources, each with its own publication date, data period, and methodology note. `.claude/agents/analyst-report-subagent.md`, `.claude/agents/news-article-subagent.md`, and `.claude/agents/gov-dataset-subagent.md` are the three real Claude Code subagents, one per source. `.claude/settings.json` + `.claude/hooks/log_tool_use.py` log every tool/subagent call a live session makes here.

## How each Task Info item is covered:

- **How source attribution is lost during summarization steps when findings are compressed without preserving claim-source mappings** — `CLAUDE.md`

  ```markdown
  ## 1. Never drop source attribution

  Every figure in your synthesis must be traceable to the subagent's `CLAIM` block it came from — source name, URL, and date. Never state a number as if it were a fact you just know.
  ```

  Verified live: every figure in the final report was stated with its source name attached — no bare, unattributed numbers anywhere in the synthesis.

- **The importance of structured claim-source mappings that the synthesis agent must preserve and merge when combining findings** — `.claude/agents/analyst-report-subagent.md`

  ```markdown
  CLAIM
  - claim: <what the claim states, in your own words>
  - value: <the number or figure, verbatim>
  - source_name: GreenDrive Analytics — 2025 U.S. EV Market Report
  - source_url: https://greendrive-analytics.example.com/reports/2025-ev-market
  - published_date: 2026-02-01
  - data_period: <the specific period this figure covers>
  - methodology: <verbatim methodology note from the document, if relevant to this claim>
  - excerpt: "<exact quoted text from the document supporting this claim>"
  ```

  Verified live: the subagent's actual reply used this exact structure for both of its claims, and the coordinator's synthesis preserved every field (source, date, methodology) rather than compressing them into a plain number.

- **How to handle conflicting statistics from credible sources: annotating conflicts with source attribution rather than arbitrarily selecting one value** — `data/analyst_report.md`, `data/news_article.md`, `data/gov_transportation_dataset.md`

  Three sources report California's full-year 2025 EV share as 38.4% (GreenDrive), "close to 35%" (Daily Circuit), and 31.2% (CA DOT) — same region, same period, genuinely different values. Verified live: the report's `## Contested Findings` section listed all three values with their sources side by side and stated "no value is favored here," rather than picking one.

- **Temporal data: requiring publication/collection dates in structured outputs to prevent temporal differences from being misinterpreted as contradictions** — `data/news_article.md`

  ```markdown
  As of June 2025, roughly 30% of new car sales in the state were electric...

  By the end of 2025, several analysts we spoke with estimated EV sales had reached somewhere in the mid-30s...
  ```

  These two figures, from the same article, could look contradictory without their dates. Verified live: the report placed the June figure in a separate `## Temporally Distinct (not a conflict)` section, explicitly reasoning that a mid-year number and a full-year number aren't in tension.

- **Requiring subagents to output structured claim-source mappings (source URLs, document names, relevant excerpts) that downstream agents preserve through synthesis** — `.claude/agents/gov-dataset-subagent.md`, `.claude/agents/news-article-subagent.md`

  Verified live: the news-article subagent's actual reply included `source_url: https://dailycircuit.example.com/articles/ev-milestone-california` and the verbatim excerpt "As of June 2025, roughly 30%..." — and the coordinator's synthesis still attributed that figure to "The Daily Circuit... according to dealership groups" rather than dropping the source once it reached the final report.

- **Structuring reports with explicit sections distinguishing well-established findings from contested ones, preserving original source characterizations and methodological context** — `CLAUDE.md`

  ```markdown
  ## Well-Established Findings
  <figures every source agrees on, or that only one source covers with no competing claim>

  ## Contested Findings
  <figures where two sources genuinely conflict for the same region/period — both values, both sources, no resolution imposed>
  ```

  Verified live: the report used these two section headers verbatim, and the Contested Findings table kept each source's own characterization — "modeled estimate," "analysts we spoke with," "DMV title records" — rather than describing all three as the same kind of number.

- **Completing document analysis with conflicting values included and explicitly annotated, letting the coordinator decide how to reconcile before passing to synthesis** — `.claude/agents/news-article-subagent.md`

  ```markdown
  The article contains more than one California figure for different points in the year — report them as separate `CLAIM` blocks with their own `data_period`, don't collapse them into a single number.
  ```

  Each subagent reports what its own document says without trying to resolve anything across sources — it's the coordinator, holding all three subagents' claims at once, that identifies the cross-source conflict and annotates it. Verified live: no subagent's reply mentioned the other sources at all.

- **Requiring subagents to include publication or data collection dates in structured outputs to enable correct temporal interpretation** — `.claude/agents/gov-dataset-subagent.md`

  ```markdown
  - published_date: 2026-03-01
  - data_period: <the specific period this figure covers>
  ```

  Verified live: every one of the gov-dataset subagent's five `CLAIM` blocks included both fields, letting the coordinator confirm all five statistics cover the identical 2025-01-01–2025-12-31 window.

- **Rendering different content types appropriately in synthesis outputs—financial data as tables, news as prose, technical findings as structured lists—rather than converting everything to a uniform format** — `CLAUDE.md`

  ```markdown
  Render the analyst report's numeric data as a small table, the news article's claims as prose (with its own hedging language like "roughly" or "close to" preserved), and the government dataset's statistics as a structured list — matching how each source itself presented the data.
  ```

  Verified live: the CA DOT's uncontested statistics appeared as a bulleted list, the cross-source numeric comparison appeared as a table, and the Daily Circuit's mid-year figure was quoted in prose with its original hedge ("roughly 30%") intact — three different renderings in one report, not one uniform format applied to everything.
