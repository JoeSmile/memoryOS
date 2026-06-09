## ADDED Requirements

### Requirement: ReAct tool call timeline

The chat UI SHALL render a tool call timeline on assistant messages when tool events are received during unified ReAct streaming.

#### Scenario: Timeline during multi-round ReAct

- **WHEN** stream emits one or more tool call and tool result data parts
- **THEN** the in-progress assistant message shows a timeline entry per tool round before final answer text completes

#### Scenario: Timeline shows success and failure

- **WHEN** a tool result indicates failure
- **THEN** the timeline entry shows a failed state without breaking message layout or streaming

#### Scenario: Direct answer without tools

- **WHEN** completion completes with RAG sources and no tool events
- **THEN** no tool timeline is shown and existing RAG citation chip behavior remains unchanged

#### Scenario: Development mode shows tool summary

- **WHEN** application runs in development mode and tool result includes a summary
- **THEN** the timeline entry expands to show the summary text

#### Scenario: Production mode collapses tool summary

- **WHEN** application runs in production mode and tool result includes a summary
- **THEN** the timeline entry shows tool name and success state without expanded summary by default

#### Scenario: RAG chips and timeline may coexist

- **WHEN** completion includes both RAG sources and tool events
- **THEN** citation chips and tool timeline both render without layout conflict

#### Scenario: Timeline after page reload from metadata

- **WHEN** user reloads conversation history and assistant message metadata contains `tool_steps`
- **THEN** tool timeline renders from persisted metadata without requiring live stream events

### Requirement: BFF forwards ReAct tool events via Data Stream

The web BFF chat route SHALL convert upstream SSE `tool_call` and `tool_result` events into AI SDK Data Stream parts consumable by the chat UI.

#### Scenario: Tool parts interleave with text

- **WHEN** upstream SSE emits tool events and token events in ReAct order
- **THEN** the BFF delivers structured tool data parts before or between text deltas without breaking Stop semantics
