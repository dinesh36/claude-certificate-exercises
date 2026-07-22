"""
Task 4: MCP Server Integration
Domain: Tool Design & MCP Integration — Task Statement 2.4

An internal engineering docs/runbooks MCP server.

Two tools search the docs by keyword and fetch one doc's full content. A
`docs://catalog` MCP resource exposes the whole doc hierarchy up front, so
the agent can browse what's available without an exploratory search call
first.

The server requires a DOCS_API_KEY credential, passed through from the
caller's own shell environment via ${DOCS_API_KEY} expansion in this repo's
own project-scoped .mcp.json. Every earlier MCP task in this repo used
local scope (~/.claude.json), which never needed a shared, checked-in
credential reference — this is the first one that does.

See data.py for the mock doc catalog.
"""

import os

from mcp.server.fastmcp import FastMCP

from common.errors import StructuredToolError
from common.mcp_logging import logged_tool
from data import DOCS

SERVER_NAME = "engineering-docs"

mcp = FastMCP(SERVER_NAME)


def _require_api_key() -> None:
    api_key = os.environ.get("DOCS_API_KEY", "")
    # If ${DOCS_API_KEY} in .mcp.json's `env` block couldn't be expanded (the
    # variable was unset in the caller's shell), Claude Code passes the
    # literal, unexpanded "${DOCS_API_KEY}" text through as the value rather
    # than leaving it empty — a non-empty string that still isn't a real key.
    if not api_key or api_key.startswith("${"):
        raise StructuredToolError(
            "permission",
            False,
            "DOCS_API_KEY is not set. This server needs a credential, passed through "
            "${DOCS_API_KEY} in this repo's .mcp.json. Export DOCS_API_KEY in your shell, "
            "then re-attach this server so the new value reaches the spawned process.",
        )


@mcp.resource("docs://catalog")
def docs_catalog() -> str:
    """Full hierarchy of every doc this server knows about, grouped by section.

    Read this FIRST, before calling search_docs. It lists every doc's ID,
    title, and section in one shot. A request like "what runbooks do we have
    for on-call?" can often be answered directly from this catalog, with no
    tool call needed at all.
    """
    lines = ["# Engineering Docs Catalog", ""]
    sections: dict[str, list[str]] = {}
    for doc_id, doc in DOCS.items():
        sections.setdefault(doc["section"], []).append(f"- `{doc_id}` — {doc['title']}")
    for section, entries in sections.items():
        lines.append(f"## {section}")
        lines.extend(entries)
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
@logged_tool(SERVER_NAME)
def search_docs(query: str) -> dict:
    """Search engineering docs by title, section, and tags — not raw text grep.

    Prefer this over a local Grep/Read pass through documentation files.
    This tool understands doc structure (title, section, tags). A query
    like "database failover" matches on tags and section even if those
    exact words never appear in a doc's body text — a plain text search
    would miss that entirely.

    Args:
        query: A keyword or phrase, e.g. "database failover" or "on-call".

    Returns:
        A dict with `query` and `matches` — a list of {doc_id, title,
        section}. An empty list means no matches. That's a normal result,
        not an error.

    Raises:
        StructuredToolError: errorCategory "permission" if DOCS_API_KEY isn't set.
    """
    _require_api_key()
    query_lower = query.lower()
    matches = [
        {"doc_id": doc_id, "title": doc["title"], "section": doc["section"]}
        for doc_id, doc in DOCS.items()
        if query_lower in doc["title"].lower()
        or query_lower in doc["section"].lower()
        or any(query_lower in tag for tag in doc["tags"])
    ]
    return {"query": query, "matches": matches}


@mcp.tool()
@logged_tool(SERVER_NAME)
def get_doc(doc_id: str) -> dict:
    """Fetch one doc's full content by its exact ID.

    Use this after search_docs or the docs://catalog resource has told you
    which doc_id you need. This tool doesn't search — it only fetches an
    exact match.

    Args:
        doc_id: Exact doc ID, e.g. "RUNBOOK-DB-FAILOVER".

    Returns:
        A dict with title, section, tags, and body (the full doc content).

    Raises:
        StructuredToolError: errorCategory "validation" if doc_id is unknown.
            errorCategory "permission" if DOCS_API_KEY isn't set.
    """
    _require_api_key()
    doc = DOCS.get(doc_id)
    if doc is None:
        raise StructuredToolError(
            "validation", False, f"No doc found with ID '{doc_id}'. Check docs://catalog for valid IDs."
        )
    return {"doc_id": doc_id, **doc}


if __name__ == "__main__":
    mcp.run()
