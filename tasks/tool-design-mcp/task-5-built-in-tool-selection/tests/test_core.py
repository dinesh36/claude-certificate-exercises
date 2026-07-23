"""Tests for core.py's enqueue/dequeue behavior."""

import pytest

from core import QueueEmptyError, dequeue_task, enqueue_task


def test_enqueue_then_dequeue_returns_same_job():
    enqueue_task("noop", {"x": 1})
    job = dequeue_task()
    assert job["name"] == "noop"


def test_dequeue_empty_queue_raises():
    with pytest.raises(QueueEmptyError):
        dequeue_task()
