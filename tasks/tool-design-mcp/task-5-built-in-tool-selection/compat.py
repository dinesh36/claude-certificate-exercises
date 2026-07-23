"""Legacy aliases for core.py, kept for callers who haven't migrated to the new names yet.

Do not add new functionality here — this module only re-exports.
"""

from core import enqueue_task as add_job
from core import dequeue_task as get_next_job
