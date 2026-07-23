"""Retry policy configuration for each job type this worker pool handles.

Policies are looked up by position, not by key: index 0 is the email job's
policy, index 1 is the report job's policy, index 2 is the cleanup job's
policy (see workers.py for how each is used). All three currently share the
same placeholder values.
"""

RETRY_POLICIES = [
    {
        "max_attempts": 3,
        "backoff_seconds": 5,
        "log_message": "retrying job",
    },
    {
        "max_attempts": 3,
        "backoff_seconds": 5,
        "log_message": "retrying job",
    },
    {
        "max_attempts": 3,
        "backoff_seconds": 5,
        "log_message": "retrying job",
    },
]
