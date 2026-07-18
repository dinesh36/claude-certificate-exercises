# CLAUDE.md

This is the **fintech billing monorepo** — a small sample project (Task Statement 3.1) demonstrating CLAUDE.md's configuration hierarchy, `@import` modularity, and `.claude/rules/` as an alternative to one monolithic file. It has two packages with genuinely different conventions: `packages/billing_api` (a payment-intake REST service) and `packages/ledger_worker` (an async ledger-posting worker).

This file is this sample project's own **project-level** config. It is nested inside the larger certification repo, so a live Claude Code session opened anywhere under here also inherits the outer repo's own root `CLAUDE.md` above this one — that's expected: it's a real instance of the same hierarchy layering this task is teaching, not something to work around.

## Universal standards

@.claude/rules/testing.md

Every package in this repo follows the testing conventions above, regardless of what package-specific rules it additionally imports (see `packages/billing_api/CLAUDE.md` and `packages/ledger_worker/CLAUDE.md`) — this file is the project-level baseline; directory-level files add to it, they never replace it.
