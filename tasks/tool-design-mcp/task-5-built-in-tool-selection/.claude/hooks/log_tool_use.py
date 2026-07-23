#!/usr/bin/env python3
"""PostToolUse hook: logs every built-in tool call this task's live sessions make.

Wired in this task folder's own .claude/settings.json. Claude Code invokes
this script once per tool call, passing a JSON payload on stdin (tool_name,
tool_input, tool_response, session_id, ...). Reuses common/logging_utils.py's
append_log so the record lands under logs/ in the same pretty-printed,
formatted-JSON shape every other task's logging already uses.
"""

import json
import sys

from common.bootstrap import find_repo_root
from common.logging_utils import append_log

payload = json.load(sys.stdin)

record = {
    "session_id": payload.get("session_id"),
    "tool_name": payload.get("tool_name"),
    "tool_input": payload.get("tool_input"),
    "tool_response": payload.get("tool_response"),
}

repo_root = find_repo_root(__file__)
log_path = repo_root / "logs" / "tool-selection" / "task-5-built-in-tool-selection.jsonl"
append_log(record, log_path)
