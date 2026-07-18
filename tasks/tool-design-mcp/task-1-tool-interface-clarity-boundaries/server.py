"""
Task 1: Tool Interface Clarity & Boundaries
Domain: 2 (Tool Design & MCP Integration) — Task Statement 2.1

A dev-workflow MCP server that fetches user stories and bug tickets from two
separate mock trackers and turns a fetched story into a development plan.

Replaces an originally ambiguous get_item(id) tool (which could return either
a story or a bug ticket depending on what happened to be at that ID, and
regularly misrouted "the export bug" to the story tracker and vice versa)
with two domain-specific fetch tools. Replaces an originally generic
create_plan(id) tool (which vaguely "did something plan-related" for any ID)
with three purpose-specific tools — identify_story_risks,
estimate_story_effort, and generate_dev_plan — each with a docstring stating
its input format, an example ID, its edge cases, and explicitly when to call
it instead of its siblings.

See data.py for the mock backlog/bug-tracker data this server reads from.
"""

from mcp.server.fastmcp import FastMCP

from common.mcp_logging import logged_tool
from data import BUG_TICKETS, USER_STORIES

SERVER_NAME = "dev-workflow-assistant"

mcp = FastMCP(SERVER_NAME)


@mcp.tool()
@logged_tool(SERVER_NAME)
def fetch_user_story(story_id: str) -> dict:
    """Fetch a feature/user story from the product backlog by its story ID.

    Use this for anything framed as a FEATURE REQUEST or USER STORY — new
    functionality the team is planning to build (e.g. "the CSV export
    story"). Do NOT use this for bug reports; call fetch_bug_ticket instead
    for anything framed as broken, unresponsive, or not working as expected.

    Args:
        story_id: Exact story ID, e.g. "STORY-101". Story IDs always start
            with "STORY-".

    Returns:
        A dict with title, description, acceptance_criteria (list), and
        dependencies (list of blocking items, empty if none).

    Raises:
        ValueError: if story_id isn't a known story. If it looks like a bug
            ticket ID instead, the error names fetch_bug_ticket as the
            correct tool to call.
    """
    story = USER_STORIES.get(story_id)
    if story is None:
        if story_id in BUG_TICKETS:
            raise ValueError(
                f"'{story_id}' is a bug ticket, not a user story — call "
                f"fetch_bug_ticket('{story_id}') instead."
            )
        raise ValueError(f"No user story found with ID '{story_id}'. Known stories: {', '.join(USER_STORIES)}.")
    return {"story_id": story_id, **story}


@mcp.tool()
@logged_tool(SERVER_NAME)
def fetch_bug_ticket(ticket_id: str) -> dict:
    """Fetch a bug ticket from the bug tracker by its ticket ID.

    Use this for anything framed as BROKEN, UNRESPONSIVE, or NOT WORKING AS
    EXPECTED (e.g. "the Safari export bug"). Do NOT use this for new feature
    requests; call fetch_user_story instead for anything framed as a feature
    or user story.

    Args:
        ticket_id: Exact ticket ID, e.g. "BUG-501". Bug ticket IDs always
            start with "BUG-".

    Returns:
        A dict with title, severity, repro_steps (list), expected, and
        actual observed behavior.

    Raises:
        ValueError: if ticket_id isn't a known bug ticket. If it looks like a
            story ID instead, the error names fetch_user_story as the
            correct tool to call.
    """
    ticket = BUG_TICKETS.get(ticket_id)
    if ticket is None:
        if ticket_id in USER_STORIES:
            raise ValueError(
                f"'{ticket_id}' is a user story, not a bug ticket — call "
                f"fetch_user_story('{ticket_id}') instead."
            )
        raise ValueError(f"No bug ticket found with ID '{ticket_id}'. Known tickets: {', '.join(BUG_TICKETS)}.")
    return {"ticket_id": ticket_id, **ticket}


@mcp.tool()
@logged_tool(SERVER_NAME)
def identify_story_risks(story_id: str) -> dict:
    """Flag scope, dependency, and specification risks in a user story BEFORE planning it.

    Call this first when starting work on a story, before generate_dev_plan
    or estimate_story_effort — catching an underspecified acceptance
    criterion or an unresolved dependency now is cheaper than discovering it
    mid-implementation. This tool does NOT produce a task breakdown (use
    generate_dev_plan) or a size estimate (use estimate_story_effort) — it
    only flags risks.

    Args:
        story_id: Exact story ID, e.g. "STORY-101".

    Returns:
        A dict with a `risks` list of short flagged concerns — an empty list
        means no risks were found.

    Raises:
        ValueError: if story_id isn't a known story.
    """
    story = USER_STORIES.get(story_id)
    if story is None:
        raise ValueError(f"No user story found with ID '{story_id}'. Known stories: {', '.join(USER_STORIES)}.")

    risks = []
    if len(story["acceptance_criteria"]) < 2:
        risks.append(
            "Underspecified: fewer than 2 acceptance criteria — scope may be too vague to plan reliably."
        )
    if story["dependencies"]:
        risks.append(f"Blocked pending: {'; '.join(story['dependencies'])}.")
    return {"story_id": story_id, "risks": risks}


@mcp.tool()
@logged_tool(SERVER_NAME)
def estimate_story_effort(story_id: str) -> dict:
    """Estimate a t-shirt-size effort (S/M/L) for a user story, with rationale.

    Use this when asked for a SIZE, ESTIMATE, or "how much work" a story is —
    it returns sizing only, not a task breakdown. Call generate_dev_plan
    instead when asked for the actual implementation steps.

    Args:
        story_id: Exact story ID, e.g. "STORY-101".

    Returns:
        A dict with `size` (one of "S", "M", "L") and `rationale` explaining
        the factors behind the size.

    Raises:
        ValueError: if story_id isn't a known story.
    """
    story = USER_STORIES.get(story_id)
    if story is None:
        raise ValueError(f"No user story found with ID '{story_id}'. Known stories: {', '.join(USER_STORIES)}.")

    criteria_count = len(story["acceptance_criteria"])
    dependency_count = len(story["dependencies"])
    score = criteria_count + 2 * dependency_count
    size = "S" if score <= 2 else "M" if score <= 4 else "L"
    return {
        "story_id": story_id,
        "size": size,
        "rationale": (
            f"{criteria_count} acceptance criteria and {dependency_count} unresolved "
            "dependencies contribute to this size."
        ),
    }


@mcp.tool()
@logged_tool(SERVER_NAME)
def generate_dev_plan(story_id: str) -> dict:
    """Generate an ordered engineering task breakdown for implementing a user story.

    Use this when asked to actually PLAN THE WORK or "break this down into
    tasks" — it returns implementation subtasks, not a size (use
    estimate_story_effort) and not a risk review (use identify_story_risks,
    ideally before calling this).

    Args:
        story_id: Exact story ID, e.g. "STORY-101".

    Returns:
        A dict with an ordered `tasks` list — one subtask per acceptance
        criterion, plus a final test-coverage subtask.

    Raises:
        ValueError: if story_id isn't a known story.
    """
    story = USER_STORIES.get(story_id)
    if story is None:
        raise ValueError(f"No user story found with ID '{story_id}'. Known stories: {', '.join(USER_STORIES)}.")

    tasks = [f"Implement: {criterion}" for criterion in story["acceptance_criteria"]]
    tasks.append(f"Write automated tests covering all {len(story['acceptance_criteria'])} acceptance criteria.")
    return {"story_id": story_id, "tasks": tasks}


if __name__ == "__main__":
    mcp.run()
