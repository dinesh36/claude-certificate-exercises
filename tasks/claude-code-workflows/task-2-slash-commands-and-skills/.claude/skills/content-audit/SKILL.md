---
name: content-audit
description: Scan every page under packages/docs_site/pages/ for broken internal links, missing sections, and stale references. Use when asked to audit, check, or review the docs site's content quality.
context: fork
---

# Content Audit

Scans `packages/docs_site/pages/` for content problems:

1. Read every `.md` file in `packages/docs_site/pages/`.
2. For each internal link (a relative path to another page in the same folder), confirm the target file exists. Flag any that don't.
3. Flag any page missing a top-level title or missing at least one `##` section heading.
4. Flag any page whose content references a package or component that no longer exists in `packages/`.

Produce one finding per problem, with the file name and a one-line description. Do not fix anything — only report.

This skill runs with `context: fork`, so the page-by-page scan happens in an isolated sub-agent. Auditing every page can surface dozens of small, verbose findings — running it forked keeps that noise out of the main conversation; only the final findings summary returns.
