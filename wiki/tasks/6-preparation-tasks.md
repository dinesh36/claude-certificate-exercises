# Preparation Tasks

### Task 1: Build a Multi-Tool Agent with Escalation Logic

**Objective:** Practice designing an agentic loop with tool integration, structured error handling, and escalation patterns.

**Steps:**
1. Define 3–4 MCP tools with detailed descriptions that clearly differentiate each tool's purpose, expected inputs, and boundary conditions. Include at least two tools with similar functionality that require careful description to avoid selection confusion.
2. Implement an agentic loop that checks stop_reason to determine whether to continue tool execution or present the final response. Handle both "tool_use" and "end_turn" stop reasons correctly.
3. Add structured error responses to your tools: include errorCategory (transient/validation/permission), isRetryable boolean, and human-readable descriptions. Test that the agent handles each error type appropriately (retrying transient errors, explaining business errors to the user).
4. Implement a programmatic hook that intercepts tool calls to enforce a business rule (e.g., blocking operations above a threshold amount), redirecting to an escalation workflow when triggered.
5. Test with multi-concern messages (e.g., requests involving multiple issues) and verify the agent decomposes the request, handles each concern, and synthesizes a unified response.

**Domains reinforced:** [Domain 1](./1-agentic-architecture) (Agentic Architecture & Orchestration), [Domain 2](./2-tool-design-mcp) (Tool Design & MCP Integration), [Domain 5](./5-context-management) (Context Management & Reliability)

---

### Task 2: Configure Claude Code for a Team Development Workflow

**Objective:** Practice configuring CLAUDE.md hierarchies, custom slash commands, path-specific rules, and MCP server integration for a multi-developer project.

**Steps:**
1. Create a project-level CLAUDE.md with universal coding standards and testing conventions. Verify that instructions placed at the project level are consistently applied across all team members.
2. Create .claude/rules/ files with YAML frontmatter glob patterns for different code areas (e.g., paths: ["src/api/**/*"] for API conventions, paths: ["**/*.test.*"] for testing conventions). Test that rules load only when editing matching files.
3. Create a project-scoped skill in .claude/skills/ with context: fork and allowed-tools restrictions. Verify the skill runs in isolation without polluting the main conversation context.
4. Configure an MCP server in .mcp.json with environment variable expansion for credentials. Add a personal experimental MCP server in ~/.claude.json and verify both are available simultaneously.
5. Test plan mode versus direct execution on tasks of varying complexity: a single-file bug fix, a multi-file library migration, and a new feature with multiple valid implementation approaches. Observe when plan mode provides value.

**Domains reinforced:** [Domain 3](./3-claude-code-workflows) (Claude Code Configuration & Workflows), [Domain 2](./2-tool-design-mcp) (Tool Design & MCP Integration)

---

### Task 3: Build a Structured Data Extraction Pipeline

**Objective:** Practice designing JSON schemas, using tool_use for structured output, implementing validation-retry loops, and designing batch processing strategies.

**Steps:**
1. Define an extraction tool with a JSON schema containing required and optional fields, an enum with an "other" + detail string pattern, and nullable fields for information that may not exist in source documents. Process documents where some fields are absent and verify the model returns null rather than fabricating values.
2. Implement a validation-retry loop: when Pydantic or JSON schema validation fails, send a follow-up request including the document, the failed extraction, and the specific validation error. Track which errors are resolvable via retry (format mismatches) versus which are not (information absent from source).
3. Add few-shot examples demonstrating extraction from documents with varied formats (e.g., inline citations vs bibliographies, narrative descriptions vs structured tables) and verify improved handling of structural variety.
4. Design a batch processing strategy: submit a batch of 100 documents using the Message Batches API, handle failures by custom_id, resubmit failed documents with modifications (e.g., chunking oversized documents), and calculate total processing time relative to SLA constraints.
5. Implement a human review routing strategy: have the model output field-level confidence scores, route low-confidence extractions to human review, and analyze accuracy by document type and field to verify consistent performance.

**Domains reinforced:** [Domain 4](./4-prompt-engineering) (Prompt Engineering & Structured Output), [Domain 5](./5-context-management) (Context Management & Reliability)

---

### Task 4: Design and Debug a Multi-Agent Research Pipeline

**Objective:** Practice orchestrating subagents, managing context passing, implementing error propagation, and handling synthesis with provenance tracking.

**Steps:**
1. Build a coordinator agent that delegates to at least two subagents (e.g., web search and document analysis). Ensure the coordinator's allowedTools includes "Task" and that each subagent receives its research findings directly in its prompt rather than relying on automatic context inheritance.
2. Implement parallel subagent execution by having the coordinator emit multiple Task tool calls in a single response. Measure the latency improvement compared to sequential execution.
3. Design structured output for subagents that separates content from metadata: each finding should include a claim, evidence excerpt, source URL/document name, and publication date. Verify that the synthesis subagent preserves source attribution when combining findings.
4. Implement error propagation: simulate a subagent timeout and verify the coordinator receives structured error context (failure type, attempted query, partial results). Test that the coordinator can proceed with partial results and annotate the final output with coverage gaps.
5. Test with conflicting source data (e.g., two credible sources with different statistics) and verify the synthesis output preserves both values with source attribution rather than arbitrarily selecting one, and structures the report to distinguish well-established from contested findings.

**Domains reinforced:** [Domain 1](./1-agentic-architecture) (Agentic Architecture & Orchestration), [Domain 2](./2-tool-design-mcp) (Tool Design & MCP Integration), [Domain 5](./5-context-management) (Context Management & Reliability)

---

[Back to Tasks index](./README.md)
