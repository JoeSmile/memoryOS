# agent-phase-ui Specification

## Purpose

Agent process visibility via SSE phase events and frontend indicators (EP09 Story 9.8 L2–L3).

## Requirements

### Requirement: Phase SSE events from runner

The chat graph runner SHALL emit `phase` SSE events at retrieve start, before model invocation, and optionally before tool execution.

#### Scenario: Phase order with RAG

- **WHEN** a RAG chat completion starts
- **THEN** client receives `start`, then `phase` with retrieve label, then optional `sources`, then `phase` with model label, then `token` events

#### Scenario: Phase before first token

- **WHEN** retrieve and model prep take measurable time
- **THEN** at least one `phase` event arrives before the first `token` event

### Requirement: BFF maps phase to AI SDK data part

The web BFF SHALL convert `phase` SSE frames to AI SDK custom data parts consumable by the chat UI.

#### Scenario: Phase data part in stream

- **WHEN** upstream emits `{"event":"phase","data":{"id":"retrieve","label":"检索知识库…"}}`
- **THEN** BFF forwards a data stream part the client can render in `AgentPhaseIndicator`

### Requirement: Tool timeline pending state

When `tool_call` is received without matching `tool_result`, the UI SHALL show a pending tool timeline row until result or stream end.

#### Scenario: Tavily pending visible

- **WHEN** stream emits `tool_call` for `tavily_search` and result is delayed
- **THEN** ToolTimeline displays a pending row with localized tool name before success or failure

### Requirement: Phase indicator accessibility

The phase indicator SHALL use `aria-live="polite"` to announce the current phase label to assistive technology.

#### Scenario: Screen reader announcement

- **WHEN** phase changes from retrieve to model
- **THEN** assistive technology receives updated polite live region text
