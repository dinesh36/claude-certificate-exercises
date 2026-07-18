"""Named-session persistence for demonstrating resumption and forking (Domain 1.7).

A session is the full `messages` list a `common.agent_loop.run_tool_loop` call
produced, saved as JSON under `<repo root>/logs/sessions/<session_id>.json`.
Resuming loads that history back as `run_tool_loop`'s `history` argument so a
conversation continues from where it left off; forking copies one session's
saved history into a new, independent session id so the original stays
untouched while a divergent follow-up explores a different direction from
the same shared baseline.
"""

import json
from pathlib import Path
from typing import Optional

from .bootstrap import find_repo_root
from .logging_utils import to_jsonable

SESSION_DIR_NAME = "logs/sessions"


def _session_path(session_id: str) -> Path:
    return find_repo_root(__file__) / SESSION_DIR_NAME / f"{session_id}.json"


def save_session(session_id: str, messages: list) -> None:
    """Persist a session's full message history, keyed by session_id."""
    path = _session_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(messages)))


def load_session(session_id: str) -> Optional[list]:
    """Load a previously saved session's message history, or None if it was never saved."""
    path = _session_path(session_id)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def fork_session(source_session_id: str, new_session_id: str) -> list:
    """Copy a saved session's history into a brand-new, independent session id.

    Raises ValueError if the source session was never saved. The new session is
    persisted immediately so it exists independently of the source even before
    any further messages are appended to it.
    """
    history = load_session(source_session_id)
    if history is None:
        raise ValueError(f"No saved session '{source_session_id}' to fork from.")
    save_session(new_session_id, history)
    return history
