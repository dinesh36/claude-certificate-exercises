"""Background worker that periodically drains the legacy matchmaking queue.

Still references LegacyMatchmakingQueue (see matchmaker.py) for one legacy
code path feeding the nightly analytics batch job.
"""

from matchmaker import LegacyMatchmakingQueue

_worker_queue = LegacyMatchmakingQueue()


def flush_legacy_queue() -> list:
    """Drain the legacy queue for the nightly analytics batch job."""
    drained = list(_worker_queue._queue)
    _worker_queue._queue.clear()
    return drained
