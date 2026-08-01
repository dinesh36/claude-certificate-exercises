# leaderboard_service conventions

Builds on the repo root `CLAUDE.md`'s universal standards. Service-specific:

- Every score-submission handler must be idempotent — dedupe by `match_id` (see `submit_match_result` in `leaderboard.py`). See `.claude/rules/testing-conventions.md` for the matching test-case requirement.
- Never mutate `_scores` directly from outside `submit_match_result` — that would bypass the idempotency dedupe check.
