---
description: Run the pre-publish checklist for this docs repo before a release
---

Run the docs pre-publish checklist:

1. List every page under `packages/docs_site/pages/` and check each one has a title and at least one section heading.
2. Flag any page that links to another page under `packages/docs_site/pages/` that does not exist.
3. Report the findings as a short checklist: pass/fail per page, with a one-line reason for each failure.

This command is project-scoped (`.claude/commands/publish-check.md`, committed to version control), so every teammate who clones this repo gets `/publish-check` without any personal setup. A personal variant of a checklist like this would instead live at `~/.claude/commands/publish-check.md` — outside version control, and invisible to teammates.
