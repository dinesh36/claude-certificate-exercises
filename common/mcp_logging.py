"""Shared MCP tool-call logging wrapper (Domain 2/5).

Wraps an MCP tool implementation so every call's server name, tool name,
input parameters, and either its successful result or the error it raised
are appended to a formatted (pretty-printed) JSON log file under logs/mcp/
— without each tool having to log itself. Built on the same append_log/
to_jsonable primitive common/agent_loop.py's agentic loop uses (see
common/logging_utils.py), so every task's execution trail — agentic loop
or MCP — lands under logs/ in the same shape.
"""

import functools
from datetime import datetime, timezone
from pathlib import Path

from .bootstrap import find_repo_root
from .logging_utils import append_log, to_jsonable

LOG_DIR_NAME = "logs/mcp"


@functools.lru_cache(maxsize=None)
def _log_file(server_name: str) -> Path:
    """One log file per (server_name, process) — cached so every call from the
    same server process within one run writes to the same file."""
    now = datetime.now(timezone.utc)
    filename = f"{server_name}-{now.strftime('%Y-%m-%d-T%H-%M-%S')}.jsonl"
    return find_repo_root(__file__) / LOG_DIR_NAME / filename


def log_mcp_call(server_name: str, tool_name: str, tool_input: dict, *, result=None, error: Exception = None) -> None:
    """Append one formatted JSON record for an MCP tool call: its server, tool
    name, input parameters, and either its result or the error it raised."""
    append_log(
        {
            "server": server_name,
            "tool": tool_name,
            "input": to_jsonable(tool_input),
            "result": to_jsonable(result) if error is None else None,
            "error": str(error) if error is not None else None,
            "is_error": error is not None,
        },
        _log_file(server_name),
    )


def logged_tool(server_name: str):
    """Decorator factory: wraps an MCP tool implementation so every call is
    logged to logs/mcp/<server_name>-<timestamp>.jsonl, then re-raises any
    exception so FastMCP still turns it into a failed tool call for the
    client — logging never masks or swallows a real failure.

    Usage — stack directly under @mcp.tool() so this decorator sees the plain
    function (name, args) rather than FastMCP's wrapped Tool object:

        @mcp.tool()
        @logged_tool("dev-workflow-assistant")
        def fetch_user_story(story_id: str) -> dict:
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            call_input = {**dict(zip(func.__code__.co_varnames, args)), **kwargs}
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                log_mcp_call(server_name, func.__name__, call_input, error=exc)
                raise
            log_mcp_call(server_name, func.__name__, call_input, result=result)
            return result

        return wrapper

    return decorator
