# Category B: Claude Code Configuration & Workflow Tasks (Domain 3)

Scaffolds a task as a small **sample project** — its own nested `CLAUDE.md` hierarchy and `.claude/` configuration — that demonstrates a Claude Code configuration mechanism. Unlike Category A, there is no Anthropic API call, no `common/` reuse, and no `main.py`/`tools.py` agentic loop anywhere in this category: the sample project's config files themselves *are* the graded artifact. Verification is a human opening a live Claude Code session with the sample folder as the working directory and trying documented sample prompts — not running a script.

`SKILL.md`'s step 1 (gather inputs) already resolved the task number, domain, and task statement text before handing off to this file — pick up from scenario proposal.

## 1. Propose scenario options and confirm with the user before building anything

The **scenario** here is the shape of the fictional sample codebase the config demonstrates against — e.g. a two-package Python monorepo, a frontend+backend web app, a data-pipeline repo, an infra+app repo. It must be new every time, same rule as Category A.

- Survey what's already been used: read the `# Task` section of every existing `tasks/claude-code-workflows/*/README.md` and note its sample-project shape. Never repeat one or thinly reskin it.
- Draft 3-4 candidate sample-project shapes for the covered task statement(s), each structurally different enough to need genuinely different configuration (different package boundaries, different conventions per area, different team-ownership stories) — not just renamed folders around the same two-package idea. Each candidate must still naturally exercise every `Knowledge of`/`Skills in` bullet for the covered task statement(s).
- Present the candidates via `AskUserQuestion` — one option per candidate, each `description` naming the concrete package/directory breakdown and which configuration mechanism it will showcase (e.g. "two packages with divergent `@import` chains" vs. "a monorepo where a new teammate's misplaced user-level config causes a diagnosable hierarchy bug"). Mark a recommended pick, wait for the user's answer before scaffolding anything.
- Carry the chosen scenario through consistently: package names, the illustrative source stub files, the CLAUDE.md conventions at each level, and any `.claude/rules/` topic files should all read as one coherent fictional codebase, not a mashup.

## 2. Compute the folder path

`tasks/claude-code-workflows/task-<N>-<kebab-slug>/` — same convention as Category A (see `CLAUDE.md`'s Task Naming & Folder Convention section).

- `<kebab-slug>` = short kebab-case rendering of the task's **type** — the configuration mechanism demonstrated (e.g. `claude-md-hierarchy-scoping`, `slash-commands-and-skills`, `path-specific-rules`) — never the sample project's fictional scenario. Same rule as Category A: the scenario only ever appears in the Implemented Tasks table's Topic column and the README's `# Task` section.

Do not reuse or renumber an existing folder. `ls tasks/claude-code-workflows/` first if unsure whether `N` is taken.

## 3. Scaffold the files

The task folder **is** a nested sample project — everything under it is the graded artifact, not supporting code for a script. Typical shape (only include what the specific task statement's bullets actually call for — don't pad the sample with unrelated mechanisms):

- A root-level `CLAUDE.md` inside the task folder — acts as that sample project's own project-level config. Because this sample nests inside the certification repo, a live Claude Code session opened here will also see the outer repo's own root `CLAUDE.md` above it in the hierarchy — call this out explicitly in the README as a real instance of the layering the task statement teaches, not a flaw to work around.
- Subdirectories with their own `CLAUDE.md` files for directory-level scoping — each one demonstrates a genuinely different convention than its parent (not a restatement), so the scoping is visibly meaningful when a reader compares them.
- `.claude/rules/*.md` files for modular topic-specific rules, referenced with `@import` syntax from whichever CLAUDE.md files the scenario calls for — only when the covered task statement's bullets mention `@import` and/or `.claude/rules/`.
- A handful of minimal, illustrative source files (a few short files in whatever language fits the scenario) — just enough that the CLAUDE.md conventions have something real to point at (e.g. a package with one file a testing or API convention would plausibly apply to). These are set dressing, not working software — do not build real logic, tests, or business functionality for them.
- Any other Claude Code config artifact a specific task statement calls for (`.claude/commands/`, `.claude/skills/`, `.claude/rules/*.md` with `paths:` frontmatter, `.claude/hooks/`, `.mcp.json`, etc.) — scaffold only what that statement's own bullets require.
- No `common/` reuse, no Anthropic client, no `tools.py`/`main.py`/agentic loop — this category produces configuration, not a runnable program.

## 4. Write README.md

<readme_template>
  <purpose>
    Same purpose as Category A's README: prove, with the real config files pasted in, that every Knowledge-of and Skills-in bullet for the covered task statement is actually implemented — plus prove the sample is genuinely testable by documenting prompts a reader can fire at a live Claude Code session.
  </purpose>

  <section id="1" name="task_statement_header">
    <format>
# Task Statement X.Y: &lt;title, copied verbatim from wiki/tasks/&lt;N&gt;-&lt;domain-slug&gt;.md&gt;
## Knowledge of
- &lt;bullet, copied verbatim&gt;
## Skills in
- &lt;bullet, copied verbatim&gt;
    </format>
    <rule>Identical rule to Category A: copy verbatim, repeat once per statement covered if the task spans more than one.</rule>
  </section>

  <separator>---</separator>

  <section id="2" name="task_brief">
    <format>
# Task
&lt;1-2 sentences: what the sample project's fictional codebase is and what configuration mechanism it demonstrates&gt;
- &lt;bullet, if needed: a specific mechanic worth calling out, e.g. a deliberate hierarchy conflict or a diagnosable misconfiguration&gt;
    </format>
    <rule>Same plain-language rule as Category A — no file references, no code, written for a reader who hasn't opened anything yet.</rule>
  </section>

  <separator>---</separator>

  <section id="3" name="how_to_verify">
    <format>
# How to verify
This task has no script to run — it's a set of Claude Code configuration files. Open a Claude Code session with this folder as the working directory, then try:

```
&lt;sample prompt 1, in plain English&gt;
```
&lt;expected observable behavior, specific enough to check pass/fail&gt;

```
/memory
```
&lt;what this should list — confirms which CLAUDE.md/rules files actually loaded for this cwd&gt;

&lt;2-3 more sample prompts total, each isolating a different bullet from the task statement&gt;
    </format>
    <rule>Every sample prompt must be something a reader can literally paste into a live Claude Code session and get a checkable answer from — not a rhetorical example. Prefer prompts that would produce a visibly WRONG answer if the configuration were broken (e.g. citing the wrong package's convention, or missing an imported rule), so the prompt actually tests the mechanism instead of just narrating it. Include at least one prompt that exercises a `Skills in` bullet about diagnosing or fixing a misconfiguration, if the task statement has one.</rule>
  </section>

  <separator>---</separator>

  <section id="4" name="implementation_info">
    <format>
# Implementation Info
&gt; One or two sentences: which file covers which concern.
## How each Task Info item is covered:
- **&lt;short label for one Knowledge-of or Skills-in bullet&gt;** — `&lt;file&gt;`

  ```
  &lt;minimal snippet — just the lines that satisfy this bullet&gt;
  ```

  &lt;one sentence on how the snippet satisfies the bullet&gt;
    </format>
    <rule>Same rule as Category A: every bullet gets exactly one entry, same order, cite by filename only (never a line number), paste the real snippet verbatim. Snippets here are usually CLAUDE.md/`.claude/rules/*.md` excerpts rather than Python.</rule>
  </section>
</readme_template>

## 5. Verify

There's no script to `uv run`. Instead:

- Re-check every `@import` reference actually resolves to a file that exists in the task folder — no dangling imports.
- Re-check every `.claude/rules/*.md` file has valid YAML frontmatter if it uses one (e.g. a `paths:` glob for a path-scoped-rules task).
- Read every nested `CLAUDE.md` back and confirm a directory-level override reads as a deliberate, explainable difference from its parent rather than a confusing contradiction.
- If you genuinely have a way to open a nested Claude Code session against the sample folder in this environment, do so and confirm the documented sample prompts behave as written. If not, say so plainly in your report — this needs a live Claude Code session to confirm interactively, the same honesty standard Category A applies when the API is out of credits. Do not claim the prompts were verified if they weren't.
- Re-open the written README.md and check every pasted snippet still matches the real file verbatim.

## 6. Update CLAUDE.md and README.md once verified

Identical to Category A's step 6 — same table format, same columns, add one row to **both** `CLAUDE.md`'s `### Implemented Tasks` table and the root `README.md`'s `# Tasks` table in the same pass:

| Domain | Task | Topic |
|---|---|---|
| `[Claude Code Configuration & Workflows](wiki/tasks/3-claude-code-workflows)` | `[Task-<N> - <Small Description>](tasks/claude-code-workflows/task-<N>-<kebab-slug>/README.md)` | `<topic>` |

- **Task** column's `<Small Description>` is the `<kebab-slug>` from step 2 (the configuration mechanism, never the scenario), de-hyphenated into sentence case.
- **Topic** is the sample project's fictional shape (e.g. "A two-package Python monorepo with divergent per-package conventions"), pulled from the task's own README `# Task` section.

Never add a row to only one of the two files — if you touch one, update the other in the same pass.
