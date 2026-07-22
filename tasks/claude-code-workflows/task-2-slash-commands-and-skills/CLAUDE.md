# CLAUDE.md

This is the **docs publishing monorepo** — a small sample project (Task Statement 3.2) demonstrating project-scoped slash commands and skills. It has two packages: `packages/docs_site` (hand-written Markdown pages served on the docs site) and `packages/api_reference_generator` (a script that generates API reference content from the live endpoint definitions).

This file is this sample project's own **project-level** config. It is nested inside the larger certification repo, so a live Claude Code session opened anywhere under here also inherits the outer repo's own root `CLAUDE.md` above this one.

## Commands and skills in this sample

- `.claude/commands/publish-check.md` — a **project-scoped slash command**, committed here so every teammate who clones this repo gets `/publish-check` for free. There is no user-scoped equivalent in this sample: a personal command would instead live in `~/.claude/commands/`, outside version control, and only that one person would have it.
- `.claude/skills/content-audit/` — runs with `context: fork`, so its verbose per-page findings are produced in an isolated sub-agent and only a summary comes back to the main conversation.
- `.claude/skills/new-page/` — uses `argument-hint` so Claude Code prompts for the required page slug when the skill is invoked without one.
- `.claude/skills/api-ref-sync/` — uses `allowed-tools` to restrict itself to read-only tools, so it can report drift between `packages/api_reference_generator` and `packages/docs_site` but can never overwrite a hand-written page itself.

Skills here handle repeatable, on-demand workflows specific to this docs repo. Universal standards that should always apply — like the testing conventions in a project's root `CLAUDE.md` — belong in `CLAUDE.md`, not in a skill; a skill is the right tool only when the workflow is invoked occasionally, not on every turn.
