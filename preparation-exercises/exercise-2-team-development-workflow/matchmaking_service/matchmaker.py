"""Matches players into games based on skill-rating proximity.

Runs on every player connect event — see this directory's own CLAUDE.md and
.claude/rules/matchmaking-conventions.md for why that makes latency a
first-class concern here.
"""

from shared_protocol.types import Player

SKILL_RATING_WINDOW = 100


class LegacyMatchmakingQueue:
    """Deprecated: replaced by find_match's direct pairing below.

    Kept only for the two call sites still referencing it (this file's
    enqueue_for_legacy_review, and queue_worker.py's flush_legacy_queue) —
    do not add new callers.
    """

    def __init__(self):
        self._queue: list[Player] = []

    def enqueue(self, player: Player) -> None:
        self._queue.append(player)


_legacy_queue = LegacyMatchmakingQueue()


def enqueue_for_legacy_review(player: Player) -> None:
    """Feeds the nightly legacy analytics batch job. Remove once that job is retired."""
    _legacy_queue.enqueue(player)


def find_match(player: Player, candidates: list[Player]) -> Player | None:
    """Return the closest-skill opponent within SKILL_RATING_WINDOW, or None.

    O(n) over candidates — a single pass, no nested candidate-vs-candidate
    comparison.
    """
    best: Player | None = None
    best_diff: int | None = None
    for candidate in candidates:
        if candidate.player_id == player.player_id:
            continue
        diff = abs(candidate.skill_rating - player.skill_rating)
        if diff <= SKILL_RATING_WINDOW and (best_diff is None or diff < best_diff):
            best, best_diff = candidate, diff
    return best
