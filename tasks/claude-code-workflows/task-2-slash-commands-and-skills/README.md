# Task Statement 3.2: Create and configure custom slash commands and skills
## Knowledge of
- Project-scoped commands in .claude/commands/ (shared via version control) vs user-scoped commands in ~/.claude/commands/ (personal)
- Skills in .claude/skills/ with SKILL.md files that support frontmatter configuration including context: fork, allowed-tools, and argument-hint
- The context: fork frontmatter option for running skills in an isolated sub-agent context, preventing skill outputs from polluting the main conversation
- Personal skill customization: creating personal variants in ~/.claude/skills/ with different names to avoid affecting teammates
## Skills in
- Creating project-scoped slash commands in .claude/commands/ for team-wide availability via version control
- Using context: fork to isolate skills that produce verbose output (e.g., codebase analysis) or exploratory context (e.g., brainstorming alternatives) from the main session
- Configuring allowed-tools in skill frontmatter to restrict tool access during skill execution (e.g., limiting to file write operations to prevent destructive actions)
- Using argument-hint frontmatter to prompt developers for required parameters when they invoke the skill without arguments
- Choosing between skills (on-demand invocation for task-specific workflows) and CLAUDE.md (always-loaded universal standards)

---

# Subject
A docs publishing monorepo sample project with two packages: `docs_site` (hand-written Markdown pages) and `api_reference_generator` (a script defining the live API endpoints). It demonstrates project-scoped slash commands and three skills, each configured with a different SKILL.md frontmatter option.
- `/publish-check` is a project-scoped slash command, committed under `.claude/commands/` so every teammate gets it for free.
- `content-audit` runs with `context: fork` to keep its verbose per-page findings out of the main conversation.
- `new-page` uses `argument-hint` to make sure Claude Code asks for a required page slug instead of guessing one.
- `api-ref-sync` uses `allowed-tools` to restrict itself to read-only tools, so it can flag drift between the two packages but can never overwrite a hand-written page.

---

# How to verify
This task has no script to run — it's a set of Claude Code configuration files. Open a Claude Code session with this folder (`tasks/claude-code-workflows/task-2-slash-commands-and-skills/`) as the working directory, then try:

```
/publish-check
```
Expected: it lists the pages under `packages/docs_site/pages/` and flags `getting-started.md`'s link to `./installation.md` as broken, since that file doesn't exist. This proves the project-scoped command is live and actually inspects the sample content, not just echoing its own instructions.

```
Can you run a content audit on the docs site?
```
Expected: this invokes the `content-audit` skill. Because it runs with `context: fork`, the page-by-page scan happens in an isolated sub-agent — you should see a compact findings summary in the main conversation (the broken `./installation.md` link, and the stale reference to a `legacy_importer` package that doesn't exist under `packages/`), not a long inline transcript of every file it opened.

```
Use the new-page skill to add a page.
```
Expected: because this invocation gives a topic but not an explicit `<page-slug>`, and the skill's `argument-hint` marks the slug as required, Claude Code should ask you to confirm the exact slug (e.g. `pricing`) before creating `packages/docs_site/pages/pricing.md` — it should not silently guess a file name.

```
Is our API reference documentation in sync with the generator?
```
Expected: this invokes `api-ref-sync`. It should report that `packages/docs_site/pages/api-overview.md` still documents `POST /v1/reports`, which no longer exists in `packages/api_reference_generator/src/generate_reference.py` (renamed to `POST /v2/reports`), and that the new `GET /v2/reports/{id}` endpoint isn't documented anywhere. It should **not** edit `api-overview.md` itself — only report the drift — because its `allowed-tools` is restricted to read-only tools.

```
I want my own personal version of content-audit that also flags passive voice, without changing it for my teammates. How do I set that up?
```
Expected: it should recommend creating a personal skill under `~/.claude/skills/` (e.g. `~/.claude/skills/content-audit-personal/`) rather than editing `.claude/skills/content-audit/SKILL.md` in this repo — `~/.claude/skills/` is user-scoped and never reaches version control, so a different name there is invisible to teammates and the shared project skill stays untouched.

---

# Implementation Info
> A docs publishing monorepo with `.claude/commands/publish-check.md` (a project-scoped command) and three skills under `.claude/skills/` — `content-audit` (`context: fork`), `new-page` (`argument-hint`), and `api-ref-sync` (`allowed-tools`) — plus two hand-written docs pages and a generator stub so the commands and skills have something real to check.
## How each Task Info item is covered:
- **Project-scoped commands in .claude/commands/ (shared via version control) vs user-scoped commands in ~/.claude/commands/ (personal)** — `.claude/commands/publish-check.md`

  ```markdown
  This command is project-scoped (`.claude/commands/publish-check.md`, committed
  to version control), so every teammate who clones this repo gets
  `/publish-check` without any personal setup. A personal variant of a
  checklist like this would instead live at `~/.claude/commands/publish-check.md`
  — outside version control, and invisible to teammates.
  ```

  The command file itself lives under the tracked `.claude/commands/`, and its own body names the untracked user-scoped alternative so the contrast is explicit, not just implied by folder location.

- **Skills in .claude/skills/ with SKILL.md files that support frontmatter configuration including context: fork, allowed-tools, and argument-hint** — `.claude/skills/content-audit/SKILL.md`, `.claude/skills/api-ref-sync/SKILL.md`, `.claude/skills/new-page/SKILL.md`

  ```yaml
  # content-audit/SKILL.md
  context: fork
  # api-ref-sync/SKILL.md
  allowed-tools: Read, Grep, Glob
  # new-page/SKILL.md
  argument-hint: <page-slug>
  ```

  Each of the three skills demonstrates exactly one of the three frontmatter options, so each option has a concrete, working example instead of a single skill trying to show all three at once.

- **The context: fork frontmatter option for running skills in an isolated sub-agent context, preventing skill outputs from polluting the main conversation** — `.claude/skills/content-audit/SKILL.md`

  ```markdown
  This skill runs with `context: fork`, so the page-by-page scan happens in an
  isolated sub-agent. Auditing every page can surface dozens of small, verbose
  findings — running it forked keeps that noise out of the main conversation;
  only the final findings summary returns.
  ```

  `content-audit` is the kind of verbose, exploratory scan `context: fork` exists for — it inspects every page individually, which would otherwise flood the main conversation with per-file detail.

- **Personal skill customization: creating personal variants in ~/.claude/skills/ with different names to avoid affecting teammates** — `README.md` ("How to verify" section, personal-variant prompt)

  ```
  I want my own personal version of content-audit that also flags passive
  voice, without changing it for my teammates. How do I set that up?
  ```

  The expected answer routes through `~/.claude/skills/content-audit-personal/` — a different name, in the untracked user-scoped location — rather than editing the shared `.claude/skills/content-audit/SKILL.md` that teammates rely on.

- **Creating project-scoped slash commands in .claude/commands/ for team-wide availability via version control** — `.claude/commands/publish-check.md`

  ```markdown
  Run the docs pre-publish checklist:

  1. List every page under `packages/docs_site/pages/` and check each one has
     a title and at least one section heading.
  2. Flag any page that links to another page under `packages/docs_site/pages/`
     that does not exist.
  ```

  `/publish-check` is committed at the project level, so it's available to every teammate the moment they clone the repo — no personal setup required.

- **Using context: fork to isolate skills that produce verbose output (e.g., codebase analysis) or exploratory context (e.g., brainstorming alternatives) from the main session** — `.claude/skills/content-audit/SKILL.md`

  ```yaml
  ---
  name: content-audit
  description: Scan every page under packages/docs_site/pages/ for broken internal links, missing sections, and stale references. Use when asked to audit, check, or review the docs site's content quality.
  context: fork
  ---
  ```

  `content-audit`'s job — scanning every page in the docs site — is exactly the "codebase analysis" style of verbose task the bullet calls out; `context: fork` runs that scan in its own sub-agent.

- **Configuring allowed-tools in skill frontmatter to restrict tool access during skill execution (e.g., limiting to file write operations to prevent destructive actions)** — `.claude/skills/api-ref-sync/SKILL.md`

  ```yaml
  ---
  name: api-ref-sync
  allowed-tools: Read, Grep, Glob
  ---
  ```

  `api-ref-sync` is restricted to read-only tools so it can never overwrite a hand-written page in `packages/docs_site/` — even when it finds drift it's confident about — enforcing "report, don't fix" at the tool-access level instead of just as an instruction.

- **Using argument-hint frontmatter to prompt developers for required parameters when they invoke the skill without arguments** — `.claude/skills/new-page/SKILL.md`

  ```yaml
  ---
  name: new-page
  argument-hint: <page-slug>
  ---
  ```
  ```markdown
  The page slug is required — it decides the file name and the derived title.
  If this skill is invoked with no argument, ask the user for the page slug
  before creating anything; do not guess a name or create a placeholder file.
  ```

  `argument-hint` documents the required parameter, and the skill body makes the enforcement explicit: no slug means asking, not guessing.

- **Choosing between skills (on-demand invocation for task-specific workflows) and CLAUDE.md (always-loaded universal standards)** — `CLAUDE.md`

  ```markdown
  Skills here handle repeatable, on-demand workflows specific to this docs
  repo. Universal standards that should always apply — like the testing
  conventions in a project's root `CLAUDE.md` — belong in `CLAUDE.md`, not in
  a skill; a skill is the right tool only when the workflow is invoked
  occasionally, not on every turn.
  ```

  This states the dividing line directly: a skill for occasional, invoked workflows (`content-audit`, `new-page`, `api-ref-sync`), `CLAUDE.md` for standards every session should always apply.
