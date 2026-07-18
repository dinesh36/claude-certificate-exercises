# packages/ledger_worker

Async worker that posts ledger entries consumed from a message queue. In addition to the project-level testing conventions inherited from the repo root, this package follows:

@../../.claude/rules/queue-conventions.md

Do not import `api-conventions.md` here — idempotency in this package means "safe to redeliver a queue message," not "safe to replay an HTTP request with the same `Idempotency-Key`," which is `billing_api`'s concern instead.
