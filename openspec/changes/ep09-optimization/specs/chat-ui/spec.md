# chat-ui Specification (Delta)

## ADDED Requirements

### Requirement: Thinking placeholder before assistant content

The chat UI SHALL display a visible thinking or processing placeholder when the client is waiting for the API after send or demo analysis, and when streaming has started but assistant text is empty.

#### Scenario: Demo analysis waiting

- **WHEN** user clicks start analysis and demo-turn request is in flight
- **THEN** a thinking indicator appears within 300ms without duplicating during active token streaming

#### Scenario: Stream submitted without text

- **WHEN** chat status is submitted or streaming and last assistant message has empty text
- **THEN** assistant bubble shows thinking animation until first token arrives

### Requirement: Agent phase indicator

The chat UI SHALL display a single-line agent phase indicator when phase data parts are received during streaming.

#### Scenario: Retrieve phase label

- **WHEN** phase data part indicates retrieve
- **THEN** UI shows localized text such as "检索知识库…" above or within the assistant message area

#### Scenario: Phase clears after tokens

- **WHEN** first token delta arrives
- **THEN** phase indicator is hidden or replaced by streaming content

### Requirement: Demo assistant messages exclude regenerate

The chat UI SHALL NOT show regenerate on assistant messages marked as demo canned responses.

#### Scenario: Demo message no regenerate

- **WHEN** assistant message metadata includes `demo.match_id`
- **THEN** regenerate control is not shown for that message even if it is the latest assistant

## MODIFIED Requirements

### Requirement: ReAct tool call timeline

The chat UI SHALL render a tool call timeline on assistant messages when tool events are received during unified ReAct streaming.

#### Scenario: Timeline during multi-round ReAct

- **WHEN** stream emits one or more tool call and tool result data parts
- **THEN** the in-progress assistant message shows a timeline entry per tool round before final answer text completes

#### Scenario: Pending tool row before result

- **WHEN** `tool_call` is received without matching `tool_result`
- **THEN** timeline shows a pending entry until result arrives or stream ends

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
