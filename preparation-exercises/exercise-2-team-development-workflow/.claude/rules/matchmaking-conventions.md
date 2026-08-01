---
paths:
  - "matchmaking_service/**"
---

# Matchmaking service conventions

- `find_match` runs on every player's connect event — avoid blocking I/O (no synchronous file/network calls) inside it or anything it calls.
- Document the Big-O of any change to the matching algorithm in the function's docstring — an accidental O(n^2) regression here is a production latency incident, not just a style nit.
- Player-facing errors from this service must never expose internal queue state (e.g. raw `LegacyMatchmakingQueue` contents) — return a generic "no match found" instead.
