"""Core task-queue primitives: enqueue and dequeue jobs from an in-memory queue."""

from collections import deque

_QUEUE = deque()


class QueueEmptyError(Exception):
    """Raised when dequeue_task is called on an empty queue."""


def enqueue_task(name: str, payload: dict) -> None:
    """Add a job to the queue. `payload` is any JSON-serializeable dict.

    Example: enqueue_task("send_email", {"to": "a@example.com"})
    """
    _QUEUE.append({"name": name, "payload": payload})


def dequeue_task() -> dict:
    """Remove and return the oldest job in the queue.

    Raises QueueEmptyError if the queue has no jobs waiting.
    """
    if not _QUEUE:
        raise QueueEmptyError("No jobs waiting in the queue.")
    return _QUEUE.popleft()


def queue_size() -> int:
    """Return the number of jobs currently waiting."""
    return len(_QUEUE)
