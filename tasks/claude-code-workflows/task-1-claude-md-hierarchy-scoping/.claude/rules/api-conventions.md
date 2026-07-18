# REST API Conventions (billing_api)

- All endpoints are versioned under `/v1/`.
- Every payment-mutating endpoint requires an `Idempotency-Key` header; replaying the same key returns the original response instead of double-charging.
- Error responses always return `{"error_code": str, "message": str}` — never a bare string or a raw stack trace.

Only `packages/billing_api` imports this file — `packages/ledger_worker` has no HTTP surface, so these conventions don't apply there.
