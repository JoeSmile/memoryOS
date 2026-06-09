## ADDED Requirements

### Requirement: Unified ReAct SSE tool events

When the unified ReAct graph executes tool calls, the SSE stream SHALL emit structured tool lifecycle events for each tool round before resuming assistant tokens.

#### Scenario: Tool events per ReAct round

- **WHEN** the model requests a tool invocation during a completion
- **THEN** SSE emits `tool_call` then `tool_result` for that round before subsequent tokens or additional tool rounds

#### Scenario: No tool events when model answers directly

- **WHEN** the model completes without requesting any tools after retrieval
- **THEN** SSE does not emit `tool_call` or `tool_result` events and may still emit RAG `sources` when retrieval qualifies

#### Scenario: Multiple tool rounds emit multiple pairs

- **WHEN** the ReAct loop executes more than one tool round before final answer
- **THEN** SSE emits a `tool_call` and `tool_result` pair for each round in order

#### Scenario: Unified stream completes with done

- **WHEN** unified ReAct stream finishes successfully
- **THEN** a final `done` event is emitted after tokens and persisted assistant metadata includes `tool_steps` when tools ran
