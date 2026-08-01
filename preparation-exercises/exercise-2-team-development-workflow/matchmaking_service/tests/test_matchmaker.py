from matchmaker import find_match
from shared_protocol.types import Player


def test_find_match_picks_closest_skill():
    me = Player(player_id=1, display_name="Nova", skill_rating=1500)
    candidates = [
        Player(player_id=2, display_name="Orion", skill_rating=1550),
        Player(player_id=3, display_name="Vega", skill_rating=1620),
    ]
    match = find_match(me, candidates)
    assert match is not None
    assert match.player_id == 2


def test_find_match_returns_none_outside_window():
    me = Player(player_id=1, display_name="Nova", skill_rating=1500)
    candidates = [Player(player_id=2, display_name="Orion", skill_rating=1800)]
    assert find_match(me, candidates) is None
