# Async Worker Conventions (ledger_worker)

- Every message handler must be idempotent — the same message may be redelivered at least once.
- Retries use exponential backoff, capped at 5 attempts, before routing to the `ledger-dlq` dead-letter queue.
- Never acknowledge a message before the ledger write it depends on has been committed.

Only `packages/ledger_worker` imports this file — `packages/billing_api` has no queue consumer, so these conventions don't apply there.
