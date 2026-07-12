"""Generic agentic tool-use loop (Domain 1.1) with concurrent, fault-tolerant
tool execution (Domain 5).

Continues while stop_reason == "tool_use", terminates on "end_turn". Does
not use an iteration cap as the primary stopping mechanism and does not
parse assistant text to detect completion.

Every tool_use block in a turn is dispatched concurrently — they may resolve
in a different order than requested (Anthropic matches each tool_result to
its tool_use by id, not by position, so this is safe) — and any dispatcher
or hook exception is caught and converted into a structured tool_error
result rather than propagating, so one failing tool call can never cause a
sibling call's result, or the whole turn's tool_result block, to go missing.
"""

import functools
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from .bootstrap import find_repo_root
from .errors import is_tool_error, tool_error

# Every exercise logs the full message transcript by default, one file per
# run, always under <repo root>/logs/.
LOG_DIR_NAME = "logs"

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
    log_file: Optional[Path] = None


def _to_jsonable(value):
    """Recursively convert SDK content blocks (pydantic models) into plain JSON-able data."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value


@functools.lru_cache(maxsize=1)
def _log_file() -> Path:
    """One log file per process run, named with a readable UTC timestamp.

    Cached so every _append_log call within a single run writes to the same file.
    """
    now = datetime.now(timezone.utc)
    filename = f"{now.strftime('%Y-%m-%d-T%H-%M-%S')}.jsonl"
    return find_repo_root(__file__) / LOG_DIR_NAME / filename


def _append_log(record: dict) -> None:
    """Append one JSON-lines record to the resolved log file, creating parent dirs as needed."""
    path = _log_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), **record}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(_to_jsonable(record)) + "\n")

def log_tool_call(tool_name: str, tool_input: dict, result: dict) -> None:
    print(f"  [tool] {tool_name}({tool_input}) -> {result}")


def _execute_tool_block(block, dispatcher: ToolDispatcher, hook: Optional[ToolHook]) -> dict:
    """Run one tool_use block, converting any dispatcher/hook exception into a
    structured tool_error instead of letting it propagate and abort the run."""
    try:
        blocked = hook(block.name, block.input) if hook else None
        result = blocked if blocked is not None else dispatcher(block.name, block.input)
    except Exception as exc:
        result = tool_error(
            "transient",
            True,
            f"Tool '{block.name}' raised an unexpected error ({exc}) instead of returning "
            "a result. Treat as transient and retry.",
        )

    log_tool_call(block.name, block.input, result)
    return {
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": str(result),
        "is_error": is_tool_error(result),
    }


def _run_tool_blocks(tool_blocks: list, dispatcher: ToolDispatcher, hook: Optional[ToolHook]) -> list[dict]:
    """Dispatch every tool_use block from one turn concurrently.

    Blocks can resolve in a different order than they were requested (e.g.
    one subagent call is slower than another) — results are collected as
    each future completes and matched back to its call via tool_use_id,
    which is all the API requires; position in the returned list is
    otherwise irrelevant.
    """
    with ThreadPoolExecutor(max_workers=len(tool_blocks)) as pool:
        futures = [pool.submit(_execute_tool_block, block, dispatcher, hook) for block in tool_blocks]
        return [future.result() for future in as_completed(futures)]


def run_tool_loop(
    client,
    model: str,
    system: str,
    tools: list[dict],
    dispatcher: ToolDispatcher,
    user_message: str,
    max_tokens: int = 2048,
    hook: Optional[ToolHook] = None,
) -> AgentResult:
    """Run the agentic loop.

    The full message transcript (every user, assistant, and tool_result turn)
    is appended as it happens to a JSON Lines log file — one JSON object per
    line, so the file is a complete audit trail even if the process is
    interrupted mid-loop. See _log_file() for how the path is resolved.
    """
    messages = [{"role": "user", "content": user_message}]
    _append_log(messages[-1])

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})
        _append_log({**messages[-1], "stop_reason": response.stop_reason})

        if response.stop_reason != "tool_use":
            break

        tool_blocks = [block for block in response.content if block.type == "tool_use"]
        tool_results = _run_tool_blocks(tool_blocks, dispatcher, hook)
        messages.append({"role": "user", "content": tool_results})
        _append_log(messages[-1])

    final_text = "".join(block.text for block in response.content if block.type == "text")
    return AgentResult(final_text=final_text, messages=messages, log_file=_log_file())
