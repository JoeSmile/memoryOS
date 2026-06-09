# agent-tools Specification

## Purpose

Unified ReAct agent tools for EP05: ToolRegistry, ToolExecutor, `tavily_search`, and the `execute_tools` graph node contract.
## Requirements
### Requirement: Tool definition schema

The system SHALL represent each agent tool with a stable name, human-readable description, and JSON Schema parameters object suitable for OpenAI-compatible function calling.

#### Scenario: Registry exposes tools for model binding

- **WHEN** the unified ReAct graph initializes `call_model` for a request
- **THEN** the tool registry provides function schemas including `tavily_search` for `bind_tools`

#### Scenario: Unknown tool rejected at execution

- **WHEN** executor receives a tool name not registered in the registry
- **THEN** execution fails with a structured error without invoking side effects

### Requirement: Tool executor validates and runs tools

The tool executor SHALL validate tool arguments against the tool JSON Schema, enforce a configurable timeout, and return structured success or error payloads as ToolMessage content.

#### Scenario: Valid arguments execute tool

- **WHEN** executor receives registered tool name and arguments matching the schema
- **THEN** the tool handler runs and returns a JSON-serializable result within the timeout

#### Scenario: Handler exception becomes tool error message

- **WHEN** a tool handler raises during execution
- **THEN** executor captures the error and returns a failure payload suitable for ToolMessage content without aborting the SSE stream

### Requirement: Tavily search built-in tool

The system SHALL provide a `tavily_search` tool for web retrieval when model-selected during ReAct loops.

#### Scenario: Search returns truncated web snippets

- **WHEN** the model invokes `tavily_search` with a non-empty query
- **THEN** the tool returns up to the configured max results with titles, URLs, and snippets for model observation

#### Scenario: Missing API key uses mock

- **WHEN** `TAVILY_API_KEY` is unset in development or harness
- **THEN** the tool returns deterministic mock results without external network calls

### Requirement: ReAct execute tools node

The unified graph SHALL include an `execute_tools` node that runs model-requested tool calls and appends ToolMessage results to graph state before the next model turn.

#### Scenario: Tool messages appended after execution

- **WHEN** `call_model` returns an assistant message with tool_calls
- **THEN** `execute_tools` runs each call via the registry and appends corresponding ToolMessage entries to state

#### Scenario: Loop respects recursion limit

- **WHEN** tool loop iterations reach the configured maximum
- **THEN** the graph terminates with a final assistant response rather than running unbounded tool cycles

