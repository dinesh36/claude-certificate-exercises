"""Tracks scores and rankings. Every score submission must be idempotent —
see this directory's own CLAUDE.md and .claude/rules/testing-conventions.md.
"""

from shared_protocol.types import MatchResult

_submitted_match_ids: set[str] = set()
_scores: dict[int, int] = {}


def submit_match_result(result: MatchResult) -> dict:
    """Record a match result. Resubmitting the same match_id is a no-op."""
    if result.match_id in _submitted_match_ids:
        return {"status": "duplicate_ignored", "match_id": result.match_id}
    _submitted_match_ids.add(result.match_id)
    _scores[result.winner_id] = _scores.get(result.winner_id, 0) + result.winner_score
    _scores[result.loser_id] = _scores.get(result.loser_id, 0) + result.loser_score
    return {"status": "recorded", "match_id": result.match_id}


def format_rank_label(rank_index: int) -> str:
    """Return a display label like '#1' for the given zero-based rank index."""
    return f"#{rank_index}"
