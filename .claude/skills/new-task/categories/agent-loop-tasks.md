# Category A: Agentic Tool-Use Tasks (Domains 1, 2, 4, 5)

Scaffolds a task as a Python script that exercises the Anthropic Messages API tool-use loop — indistinguishable in structure from the existing ones: same folder naming, same file split, same `common/` reuse, same README.md shape. The canonical reference implementation is [`tasks/agentic-architecture/task-1-multi-tool-agent-escalation/`](../../../../tasks/agentic-architecture/task-1-multi-tool-agent-escalation/) (tools with no client/model needed). Read its `README.md`, `main.py`, `tools.py`, `policy.py`, and `data.py` before scaffolding a new task if you have not already read them in this session. If the new task's tools need to make their own Anthropic calls (e.g. dispatching subagents), also read [`task-2-coordinator-subagent-orchestration/tools.py`](../../../../tasks/agentic-architecture/task-2-coordinator-subagent-orchestration/tools.py) for the self-contained-client pattern (see step 3's `tools.py` entry below).

`SKILL.md`'s step 1 (gather inputs) already resolved the task number, domain(s), and task statement text before handing off to this file — pick up from scenario proposal.

## 1. Propose scenario options and confirm with the user before building anything

Structure (file split, `common/` reuse, README shape) stays identical across tasks. The **scenario** — the fictional domain the agent/tools operate in, e.g. task-1's electronics-retailer customer-support agent — must be new every time, and the specific choice is the user's to make, not yours to assume.

- Survey what's already been used first: read the module docstring of every existing `tasks/*/*/main.py` (e.g. `head -n 12 tasks/*/*/main.py`) and note each one's scenario (customer support/refunds, remote-work research, trip planning, etc.). Never propose one of these, and never propose a thin reskin of one (e.g. don't propose "customer support for a software subscription" alongside "customer support for electronics" — that's the same idea with new nouns).
- Draft 3-4 candidate scenarios for the covered task statement(s), each from a genuinely different industry/workflow (draw from: incident/on-call response, healthcare appointment scheduling, DevOps deployment approval, library/inventory management, hiring/recruiting, restaurant reservations, fitness coaching, IoT device fleet management, financial trading compliance, content moderation, product-review research, or similar — anything not already used in the repo). Each candidate must still naturally exercise every `Knowledge of`/`Skills in` bullet for the covered task statement(s); the scenario is flavor, the bullets are the requirement.
- Present the candidates to the user with `AskUserQuestion` — one question, one option per candidate, each option's `description` naming the concrete document/data set, subagent or tool breakdown, and any fork/divergent-output structure so the user can tell the options apart at a glance (see task-3's product-review/restaurant/hiring/trip-planner options for the shape to match). Mark your own top pick "(Recommended)" but let the user choose. Do not scaffold any files until they answer.
- Carry the chosen scenario through consistently: the mock data (`data.py`), tool names/descriptions (`tools.py`), any policy hook (`policy.py`), and the system prompt (`main.py`) should all read as one coherent scenario, not a mashup.

## 2. Compute the folder path

`tasks/<domain-slug>/task-<N>-<kebab-slug>/`

- `<domain-slug>` = slug of the domain the task belongs to — see domain-slug table in `CLAUDE.md`.
- `<kebab-slug>` = short kebab-case rendering of the task's **type** (the architecture pattern/mechanism it demonstrates, e.g. `coordinator-subagent-orchestration`, `hooks-data-normalization`) — never the fictional scenario/topic chosen in step 1. The scenario belongs only in the Implemented Tasks table's Topic column and the README's `# Task` section; two tasks with the same type but different scenarios should still read as "the same kind of folder name."

Do not reuse or renumber an existing folder. If unsure whether `N` is already taken, `ls tasks/<domain-slug>/` first — `task-<N>` numbers must stay unique within a domain's folder (they restart at 1 per domain).

## 3. Scaffold the files

Split code by concern, matching the reference task. Not every task needs every file — only add a module if the task actually has that concern:

- `main.py` — required. Module docstring's first line is `Task <N>: <Title>`, where `<Title>` is a title-cased rendering of the same `<kebab-slug>` (step 2) — the task's type, never the scenario — e.g. slug `multi-step-enforcement-handoff` → title `Multi-Step Enforcement & Handoff` (keep compound-word hyphens that read as one adjective like "Multi-Step"; join the last two components with "&" when the slug reads as two joined ideas, matching task-2 through task-5's titles). This title must also be the Implemented Tasks table's Task-column description (step 6). Second line names the domain(s); then a 2-3 sentence summary of what it demonstrates. Imports the Anthropic client and loop primitives from `common/` (never re-implement client setup or the tool-use loop locally). Imports `TOOLS` from `tools.py` and passes it straight to `run_tool_loop(tools=TOOLS, ...)` — every task's `main.py` has this exact same shape, since `tools.py` is always fully self-contained (see below); there is never any binding or dispatcher-building logic in this file. Defines the system prompt. `if __name__ == "__main__":` accepts an optional `sys.argv[1]` scenario override with a sensible default, runs the loop, and prints the result.
- `tools.py` — if the task defines tools. Its **only export is `TOOLS`**: a list of `{"schema": <Anthropic tool schema dict>, "implementation": <callable>}` entries, one per tool, where every `implementation` is a plain `(**tool_input) -> dict` callable — fully ready to call, nothing left to bind. Tool implementation functions are private (`_leading_underscore`, e.g. `_get_order_details`) since nothing outside this module imports them individually anymore. If an implementation needs a client/model (e.g. subagent-dispatch tools like task-2/task-3's), `tools.py` builds its own at module load time — `_client = get_client()`, `_model = DEFAULT_MODEL` — and the implementation functions close over those directly instead of taking `client`/`model` as parameters; this binding work stays entirely in `tools.py`, never in `main.py`. If any other file (e.g. `policy.py`) needs to read/write shared mutable state a tool implementation touches (like task-4's `verified_approvals` set), put that state in `data.py`, not `tools.py` — `tools.py` cannot have a second export. Use `common.errors.tool_error(...)` for every failure path inside the implementations themselves — never return a bare `"Operation failed"` string.
- `policy.py` — if the task needs a programmatic pre-call hook (business rule enforced deterministically rather than left to the model/prompt) — wired in as `pre_hook=...` on `run_tool_loop`.
- `normalize.py` — if the task needs a programmatic post-call hook (e.g. normalizing heterogeneous data formats from different tools before the model sees them) — wired in as `post_hook=...` on `run_tool_loop`.
- `data.py` — if the task needs a mock data store (and/or shared mutable state read by both `tools.py` and `policy.py`/`normalize.py`).
- Any other module the task genuinely needs — keep the same "one concern per file, short module docstring naming which domain/task statement it demonstrates" pattern.

Reuse from `common/`:
- `common.client.get_client()` / `DEFAULT_MODEL` — Anthropic client + model. Both `main.py` (for the coordinator's own `run_tool_loop` call) and, if needed, `tools.py` (for subagent calls) construct their own client this way — two client instances in the same process is fine, it's a lightweight object.
- `common.agent_loop.run_tool_loop` — the agentic loop (terminates on `stop_reason != "tool_use"`; never gate termination on an iteration cap or on parsing assistant text). Its `tools` argument is a `TOOLS`-shaped list (see `tools.py` above); it extracts every `schema` for the Anthropic API call and builds its own internal name → implementation map from `implementation` to dispatch `tool_use` blocks directly — there is no separate dispatcher to construct or pass anywhere. Takes optional `pre_hook` (blocks a call before dispatch) and `post_hook` (transforms a successful result before the model sees it).
- `common.errors.tool_error()` / `is_tool_error()` — structured tool error shape (`errorCategory`, `isRetryable`, `description`).
- `common.bootstrap.find_repo_root()` — path resolution.

If the task needs a genuinely new reusable primitive (e.g. multi-agent coordination helpers for a Domain 1.2/1.3 task), add it to `common/` rather than inlining it in the task folder — but only if it will plausibly be reused by another task, not as a place to dump task-specific logic.

## 4. Write README.md

<readme_template>
  <purpose>
    The README.md is the graded artifact: it proves, with real code snippets, that every Knowledge-of and Skills-in bullet for the covered task statement(s) is actually implemented. A reviewer should be able to open the README and see the exact code satisfying each bullet without needing to open the source files.
  </purpose>

  <section id="1" name="task_statement_header">
    <format>
# Task Statement X.Y: &lt;title, copied verbatim from wiki/tasks/&lt;N&gt;-&lt;domain-slug&gt;.md&gt;
## Knowledge of
- &lt;bullet, copied verbatim&gt;
## Skills in
- &lt;bullet, copied verbatim&gt;
    </format>
    <rule>Copy the heading and every bullet verbatim from the wiki domain file — do not paraphrase. If the task spans multiple task statements or domains, repeat this whole block once per statement covered, in domain order.</rule>
  </section>

  <separator>---</separator>

  <section id="2" name="task_brief">
    <format>
# Task
&lt;1-2 sentences: what the task's fictional scenario is and what business logic it implements&gt;
- &lt;bullet, if needed: a specific mechanic worth calling out&gt;
- &lt;bullet, if needed: another specific mechanic worth calling out&gt;
    </format>
    <rule>This is a plain-language orientation for a human reader, written before they've looked at any code — no file references, no code, no task-statement jargon. State the scenario (what domain/business is this pretending to be) and what it actually does, in 1-2 sentences; add bullets only for mechanics specific enough that "what the task does" would be incomplete without them (e.g. a policy threshold, a deliberately-flaky demo path, a fork into divergent outputs). Skip bullets entirely if the 1-2 sentences already say enough.</rule>
  </section>

  <separator>---</separator>

  <section id="3" name="how_to_run">
    <format>
# How to run
See the repository root [README](../../../README.md) for one-time setup (uv project, `ANTHROPIC_API_KEY`).
```bash
uv run tasks/&lt;domain-slug&gt;/task-&lt;N&gt;-&lt;slug&gt;/main.py
```
    </format>
    <rule>If main.py accepts an optional scenario argument, add 2-3 further `uv run ... "custom message"` examples, each exercising a visibly distinct code path (e.g. happy path, a validation error, a policy-blocked/escalation path) — not just cosmetic variations of the same path.</rule>
  </section>

  <separator>---</separator>

  <section id="4" name="implementation_info">
    <format>
# Implementation Info
&gt; One or two sentences: which file covers which concern.
## How each Task Info item is covered:
- **&lt;short label for one Knowledge-of or Skills-in bullet&gt;** — `&lt;file.py&gt;`

  ```python
  &lt;minimal snippet — just the lines that satisfy this bullet&gt;
  ```

  &lt;one sentence on how the snippet satisfies the bullet&gt;
    </format>
    <rule>Every bullet from every "Knowledge of" and "Skills in" list quoted in section 1 must have exactly one corresponding entry here, in the same order. Cite the file by name only (`tools.py`, `../../../common/agent_loop.py`, etc.) — never a line number or line-range link. Line numbers drift as soon as any file in the repo is edited again (including shared `common/` files touched by a later task), which silently breaks every prior README that pointed at a line range; a bare filename never goes stale. Paste the actual snippet (copy it from the real file, don't paraphrase or reconstruct it from memory) and trim it to just the lines that demonstrate the bullet — a few lines, not the whole function, unless the whole function is genuinely that short.</rule>
  </section>
</readme_template>

## 5. Verify

Run `uv run tasks/<domain-slug>/task-<N>-<slug>/main.py` from the repo root and confirm it executes end to end (or report exactly why it can't — e.g. missing `ANTHROPIC_API_KEY`, out of credits). If a live run isn't possible, fall back to direct static validation instead of assuming success: import and invoke every tool implementation and hook directly with realistic inputs, feed a simulated exception through `common.agent_loop._execute_tool_block` to confirm it converts to a structured retryable error, validate the `TOOLS` list shape, and `py_compile` every changed file — then report the actual API status honestly rather than claiming a live run succeeded. Either way, re-open the written README.md and check every pasted snippet still matches the real file verbatim.

## 6. Update CLAUDE.md and README.md once verified

Only after step 5 actually passes — this table is for done, working tasks, not scaffolded-but-unverified ones. Add one row to **both** `CLAUDE.md`'s `### Implemented Tasks` table and the root `README.md`'s `# Tasks` table — same three columns, same row, in both places, since they must always match:

| Domain | Task | Topic |
|---|---|---|
| `[<Domain Name>](wiki/tasks/<N>-<domain-slug>)` | `[Task-<N> - <Small Description>](tasks/<domain-slug>/task-<N>-<kebab-slug>/README.md)` | `<topic>` |

- **Domain** — the domain's full name (e.g. "Agentic Architecture & Orchestration"), linked to its `wiki/tasks/<N>-<domain-slug>` file (match the link style already used by the existing table rows).
- **Task** — `Task-<N> - <Small Description>` as the single link text (e.g. `Task-1 - Multi tool agent escalation`), linked to the task's own `README.md`. `<Small Description>` is the same `<kebab-slug>` chosen in step 2 (the task's **type**), just de-hyphenated into sentence case (acronyms like "IT" kept uppercase) — e.g. kebab-slug `multi-step-enforcement-handoff` → `Multi step enforcement handoff`. This must match `main.py`'s docstring title (above) and never the scenario.
- **Topic** — one line, 10 words max, naming the fictional business scenario (e.g. "A customer-support agent for an online electronics retailer") — pull this from the task's own README `# Task` section, don't restate the Task Statement text.

Never add a row to only one of the two files — if you touch one, update the other in the same pass.
