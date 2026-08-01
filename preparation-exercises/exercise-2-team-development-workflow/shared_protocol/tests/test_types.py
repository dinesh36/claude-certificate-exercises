from shared_protocol.types import MatchResult, Player


def test_player_construction():
    player = Player(player_id=1, display_name="Nova", skill_rating=1500)
    assert player.player_id == 1
    assert player.skill_rating == 1500


def test_match_result_construction():
    result = MatchResult(match_id="M-1", winner_id=1, loser_id=2, winner_score=10, loser_score=6)
    assert result.winner_id != result.loser_id
