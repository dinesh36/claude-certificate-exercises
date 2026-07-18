"""Shared JSON-Lines log-file primitive (Domain 5).

Both the Anthropic agentic loop (common/agent_loop.py) and MCP server tasks
(common/mcp_logging.py) append through `append_log` below, so every task's
execution trail lands under logs/ in the same shape: one JSON object per
line, written as it happens so the file is a complete audit trail even if
the process is interrupted mid-run.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


def to_jsonable(value):
    """Recursively convert SDK content blocks (pydantic models) into plain JSON-able data."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value


def append_log(record: dict, path: Path) -> None:
    """Append one JSON-Lines record to `path`, stamping it with a timestamp and
    creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), **record}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(to_jsonable(record)) + "\n")
