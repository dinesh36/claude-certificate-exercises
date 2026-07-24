"""Tests for config.py's retry policy list."""

from config import RETRY_POLICIES


def test_has_one_policy_per_job_type():
    assert len(RETRY_POLICIES) == 3


def test_each_policy_has_required_keys():
    for policy in RETRY_POLICIES:
        assert {"max_attempts", "backoff_seconds", "log_message"} <= policy.keys()
