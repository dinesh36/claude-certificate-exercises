---
name: new-page
description: Scaffold a new hand-written docs page under packages/docs_site/pages/ with the standard title and section headings.
argument-hint: <page-slug>
---

# New Page

Scaffolds a new page at `packages/docs_site/pages/<page-slug>.md` with:

```markdown
# <Title, derived from page-slug>

## Overview

## Usage

## See also
```

The page slug is required — it decides the file name and the derived title. If this skill is invoked with no argument, ask the user for the page slug before creating anything; do not guess a name or create a placeholder file.
