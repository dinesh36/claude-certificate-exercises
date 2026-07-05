# [Claude Certified Architect – Foundations](https://anthropic-partners.skilljar.com/claude-certified-architect-foundations-certification)

According to this [exam guide](./wiki/exam-guide.pdf) claude suggested few exercises here, This repository contains the respective exercise implementation 

# [Claude Exercises](./wiki/exercises/README.md)

# Setup

This repository uses a single [uv](https://docs.astral.sh/uv/) project at the root for all exercises — dependencies and the shared [`common/`](./common) package are managed here, not per exercise.

1. Add your `ANTHROPIC_API_KEY` to a `.env` file at the repository root (gitignored).
2. Run any exercise from the repository root, e.g.:

   ```bash
   uv run exercises/agentic-architecture/task-1-multi-tool-agent-escalation/main.py
   ```