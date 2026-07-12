"""Isolated single-turn subagent invocation (Domain 1.2).

A subagent call is a fresh Anthropic request with its own system prompt and
a fresh message list — it never receives the coordinator's conversation
history automatically. Any context the subagent needs (the subtopic, prior
findings to build on, etc.) must be explicitly included in `user_message` by
the caller.
"""

from anthropic import Anthropic


def run_subagent(client: Anthropic, model: str, system: str, user_message: str, max_tokens: int = 1024) -> str:
    """Run one isolated, tool-free subagent turn and return its text output."""
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
