"""Minimal illustrative stub for the ledger_worker package (Task Statement 3.1 sample).

Not a working worker — just enough shape for packages/ledger_worker/CLAUDE.md's
queue conventions (idempotent handlers, retry/backoff, dead-letter routing) to
have something concrete to point at.
"""


def handle_ledger_message(message: dict) -> None:
    """Would be the idempotent queue-message handler in a real worker."""
    raise NotImplementedError
