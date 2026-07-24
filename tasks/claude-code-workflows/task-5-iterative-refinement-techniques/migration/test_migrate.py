"""Seed test file. Growing this file before touching migrate.py's
implementation is the point of the TDD-iteration exercise in this task's
README — see 'How to verify'.
"""
from migrate import normalize_phone


def test_normalize_phone_strips_punctuation():
    assert normalize_phone("(415) 555-2671") == "+14155552671"
