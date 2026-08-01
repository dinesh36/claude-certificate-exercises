"""Preparation Exercise 2: MCP server for the game backend's ops/on-call status board.

Domains reinforced: 3 (Claude Code Configuration & Workflows), 2 (Tool Design & MCP Integration)

Exposes get_server_status/list_active_incidents so a live Claude Code session
working in this monorepo can check game-server health without leaving the
editor. Registered at project scope via .mcp.json with ${GAMEOPS_API_KEY}
credential expansion (Step 4) — the README also separately demonstrates user
scope for the personal/experimental-server angle.
"""

import os

from mcp.server.fastmcp import FastMCP

from common.errors import StructuredToolError
from common.mcp_logging import logged_tool

from data import INCIDENTS, SERVERS

SERVER_NAME = "game-ops"

mcp = FastMCP(SERVER_NAME)


def _require_api_key() -> None:
    api_key = os.environ.get("GAMEOPS_API_KEY", "")
    # If ${GAMEOPS_API_KEY} in .mcp.json's `env` block couldn't be expanded
    # (unset in the caller's shell), Claude Code passes the literal,
    # unexpanded "${GAMEOPS_API_KEY}" text through rather than leaving it
    # empty — a non-empty string that still isn't a real key.
    if not api_key or api_key.startswith("${"):
        raise StructuredToolError(
            "permission",
            False,
            "GAMEOPS_API_KEY is not set. Export it before calling any game-ops tool.",
        )


@mcp.tool()
@logged_tool(SERVER_NAME)
def get_server_status(server_id: str) -> dict:
    """Fetch health/status for a SINGLE game server cluster by its exact ID
    (format 'SRV-XXXX'), e.g. because it was named in an alert. Returns
    region, player count, and current status. Do NOT use this to browse
    servers by region — use list_active_incidents to see what's currently
    affected, or get the exact server ID first.
    """
    _require_api_key()
    server = SERVERS.get(server_id)
    if server is None:
        raise ValueError(f"No server found with ID '{server_id}'. Use list_active_incidents to see what's affected.")
    return {"server_id": server_id, **server}


@mcp.tool()
@logged_tool(SERVER_NAME)
def list_active_incidents(region: str = "") -> dict:
    """List currently open incidents across the game backend, optionally
    filtered by region (e.g. 'us-east', 'eu-west'). Use this to see what's
    affected right now before checking an individual server's status with
    get_server_status.
    """
    _require_api_key()
    matches = [i for i in INCIDENTS if i["status"] == "open" and (i["region"] == region if region else True)]
    return {"region": region or "all", "incidents": matches}


if __name__ == "__main__":
    mcp.run()
