---
paths:
  - "**/tests/**"
---

# Testing conventions

- Every test file mirrors the module it tests: `tests/test_<module>.py` for `<module>.py`.
- Idempotency-sensitive handlers (e.g. `leaderboard_service`'s `submit_match_result`) must include a duplicate-submission test case, not just the happy path.
- Use plain `assert` statements (pytest style) — no `unittest.TestCase` subclasses.
