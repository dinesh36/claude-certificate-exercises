"""Generic agentic tool-use loop (Domain 1.1).

Continues while stop_reason == "tool_use", terminates on "end_turn". Does
not use an iteration cap as the primary stopping mechanism and does not
parse assistant text to detect completion.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional

from .errors import is_tool_error

# (tool_name, tool_input) -> result payload (dict). Raise nothing — return a
# common.errors.tool_error(...) dict on failure instead.
ToolDispatcher = Callable[[str, dict], dict]

# (tool_name, tool_input) -> error dict to short-circuit execution, or None
# to let the dispatcher run the tool normally. Used for programmatic policy
# hooks (e.g. blocking a refund above a threshold) that must be enforced
# deterministically rather than left to the model's judgment.
ToolHook = Callable[[str, dict], Optional[dict]]

# (tool_name, tool_input, result) -> None. Called after every tool
# execution, useful for logging/observability.
ToolObserver = Callable[[str, dict, dict], None]


@dataclass
class AgentResult:
    final_text: str
    messages: list = field(default_factory=list)


def run_tool_loop(
    client,
    model: str,
    system: str,
    tools: list[dict],
    dispatcher: ToolDispatcher,
    user_message: str,
    max_tokens: int = 2048,
    hook: Optional[ToolHook] = None,
    on_tool_call: Optional[ToolObserver] = None,
) -> AgentResult:
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            blocked = hook(block.name, block.input) if hook else None
            result = blocked if blocked is not None else dispatcher(block.name, block.input)

            if on_tool_call:
                on_tool_call(block.name, block.input, result)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                    "is_error": is_tool_error(result),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    final_text = "".join(block.text for block in response.content if block.type == "text")
    return AgentResult(final_text=final_text, messages=messages)
