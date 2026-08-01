from leaderboard import format_rank_label, submit_match_result
from shared_protocol.types import MatchResult


def test_submit_match_result_records_once():
    result = MatchResult(match_id="M-100", winner_id=1, loser_id=2, winner_score=10, loser_score=4)
    first = submit_match_result(result)
    assert first["status"] == "recorded"


def test_submit_match_result_is_idempotent():
    result = MatchResult(match_id="M-101", winner_id=1, loser_id=2, winner_score=10, loser_score=4)
    submit_match_result(result)
    second = submit_match_result(result)
    assert second["status"] == "duplicate_ignored"


def test_format_rank_label_top_player():
    assert format_rank_label(0) == "#1"
