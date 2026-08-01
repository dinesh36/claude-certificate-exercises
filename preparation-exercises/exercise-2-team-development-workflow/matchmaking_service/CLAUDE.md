# matchmaking_service conventions

Builds on the repo root `CLAUDE.md`'s universal standards. Service-specific:

- Latency-sensitive: `find_match` runs on every player connect event. See `.claude/rules/matchmaking-conventions.md` (auto-loaded for any file under this directory) for the no-blocking-I/O and Big-O documentation rules.
- Never give `LegacyMatchmakingQueue` (in `matchmaker.py`) new callers — it's deprecated and scheduled for removal. It currently has two: `enqueue_for_legacy_review` here and `flush_legacy_queue` in `queue_worker.py`.
