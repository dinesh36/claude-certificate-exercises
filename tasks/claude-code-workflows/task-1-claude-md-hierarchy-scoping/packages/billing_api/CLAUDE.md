# packages/billing_api

REST API for payment intake. In addition to the project-level testing conventions inherited from the repo root, this package follows:

@../../.claude/rules/api-conventions.md

Do not import `queue-conventions.md` here — that governs `ledger_worker`, a different package with different failure semantics (a dropped HTTP request is retried by the caller; a dropped queue message needs explicit redelivery instead).
