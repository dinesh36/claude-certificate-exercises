---
name: patch-notes-draft
description: Draft player-facing patch notes from the working tree's recent changes. Use when asked to draft, write, or summarize patch notes or changelog entries for a game update.
context: fork
allowed-tools: Read, Grep, Bash
---

# Patch Notes Draft

Summarizes the current uncommitted changes (or the last N commits, if asked) into short, player-facing patch notes — not a raw commit-message dump.

1. Run `git diff` (or `git log -<N> --stat` if asked about committed history) to see what actually changed.
2. Group changes by service (`matchmaking_service`, `leaderboard_service`, `shared_protocol`) rather than by file.
3. Write 1-2 sentences per group in plain, player-facing language — no internal function or class names (e.g. "Matchmaking now pairs players more precisely by skill rating," not "changed SKILL_RATING_WINDOW in find_match").
4. Return the draft as your final message. Do not commit, push, or modify any files.
