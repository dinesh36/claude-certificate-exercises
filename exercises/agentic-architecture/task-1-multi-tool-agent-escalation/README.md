# Task Info

### Task Statement 1.1: Design and implement agentic loops for autonomous task execution

**Knowledge of:**
- The agentic loop lifecycle: sending requests to Claude, inspecting stop_reason ("tool_use" vs "end_turn"), executing requested tools, and returning results for the next iteration
- How tool results are appended to conversation history so the model can reason about the next action
- The distinction between model-driven decision-making (Claude reasons about which tool to call next based on context) and pre-configured decision trees or tool sequences

**Skills in:**
- Implementing agentic loop control flow that continues when stop_reason is "tool_use" and terminates when stop_reason is "end_turn"
- Adding tool results to conversation context between iterations so the model can incorporate new information into its reasoning
- Avoiding anti-patterns such as parsing natural language signals to determine loop termination, setting arbitrary iteration caps as the primary stopping mechanism, or checking for assistant text content as a completion indicator

---

# How to run

This exercise has no dependencies of its own — packages are managed by the `uv` project at the repository root.

1. From the repository root, make sure `ANTHROPIC_API_KEY` is set in the root `.env` file.
2. Run:

   ```bash
   uv run exercises/agentic-architecture/task-1-multi-tool-agent-escalation/main.py
   ```

   Optionally pass a custom user message as the first argument:

   ```bash
   uv run exercises/agentic-architecture/task-1-multi-tool-agent-escalation/main.py "Your custom support request here"
   ```
