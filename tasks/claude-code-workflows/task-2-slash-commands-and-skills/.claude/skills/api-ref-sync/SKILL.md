---
name: api-ref-sync
description: Compare the endpoints defined in packages/api_reference_generator against the hand-written endpoint docs in packages/docs_site to flag drift. Use when asked whether the API reference docs are out of date.
allowed-tools: Read, Grep, Glob
---

# API Reference Sync Check

Compares two sources of truth:

1. Read the endpoint definitions in `packages/api_reference_generator/src/generate_reference.py`.
2. Read the hand-written endpoint descriptions in `packages/docs_site/pages/`.
3. Report every mismatch: an endpoint that changed path, method, or was renamed/removed on the generator side but is still described differently (or not updated) in the hand-written docs.

Report drift only. Do not edit any file in `packages/docs_site/pages/` or `packages/api_reference_generator/` yourself, even if the fix looks obvious.

`allowed-tools` on this skill is restricted to `Read`, `Grep`, `Glob` — read-only tools. That's a deliberate restriction, not an oversight: the hand-written pages under `packages/docs_site/` are maintained by a technical writer, and this skill must never overwrite their wording, even to "fix" drift it finds. It can only surface the mismatch for a human to resolve.
