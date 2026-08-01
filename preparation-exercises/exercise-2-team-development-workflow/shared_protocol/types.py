"""Shared data types used by both matchmaking_service and leaderboard_service.

Neither service should redefine these — import from here so a field change
(see the README's plan-mode migration prompt) only needs to happen once.
"""

from dataclasses import dataclass


@dataclass
class Player:
    player_id: int
    display_name: str
    skill_rating: int


@dataclass
class MatchResult:
    match_id: str
    winner_id: int
    loser_id: int
    winner_score: int
    loser_score: int
