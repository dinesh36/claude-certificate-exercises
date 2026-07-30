"""Reading tool_use blocks off a raw Anthropic response (Domain 4.3).

For tasks that call `client.messages.create(tools=..., tool_choice=...)`
directly instead of going through `common/agent_loop.py`'s tool-use loop —
which already reads and dispatches `tool_use` blocks internally, so it has
no need for this.
"""

from typing import Any


def first_tool_use_block(response: Any) -> Any:
    """Return the first tool_use content block in a response.

    Raises ValueError (naming the actual stop_reason) if the model replied
    with text instead of calling a tool — e.g. a forced or "any" tool_choice
    the model still didn't satisfy.
    """
    for block in response.content:
        if block.type == "tool_use":
            return block
    raise ValueError(f"model did not call a tool (stop_reason={response.stop_reason})")
