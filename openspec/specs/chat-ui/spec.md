# chat-ui Specification

## Purpose

Single-session analysis chat shell for EP02 Phase 7: message stream, Markdown, management hooks, no sidebar.
## Requirements
### Requirement: Single-session chat layout without sidebar

The web application SHALL provide a chat page focused on one conversation at a time without a multi-conversation sidebar.

#### Scenario: Open conversation by id

- **WHEN** user navigates to `/chat?conversation_id=<uuid>` while authenticated
- **THEN** main area loads that conversation history and subsequent messages use the same id

#### Scenario: Create conversation when id missing

- **WHEN** user opens `/chat` without `conversation_id`
- **THEN** system creates a conversation and redirects with `conversation_id` in the query string

### Requirement: Message identity and management hooks

Messages in the UI SHALL use stable server-issued `id` values as React keys and SHALL expose management affordances for analysis workflows.

#### Scenario: Stable keys

- **WHEN** messages are rendered from API or stream completion
- **THEN** each row uses `message.id` from persistence, not array index

#### Scenario: Regenerate assistant message

- **WHEN** user triggers regenerate on the latest assistant message
- **THEN** client initiates a new completion for the conversation without breaking message list integrity

### Requirement: Context visibility indicator

The chat UI SHALL display a read-only indicator of how many messages are loaded for the current conversation.

#### Scenario: Show loaded message count

- **WHEN** conversation history is displayed
- **THEN** UI shows the count of persisted messages (e.g. "N 条消息已载入上下文")

### Requirement: Markdown rendering for assistant messages

Assistant messages SHALL be rendered with Markdown including GFM features after streaming completes.

#### Scenario: Render completed message

- **WHEN** assistant message streaming completes
- **THEN** message content is rendered as Markdown with readable code blocks

### Requirement: Client state with Zustand

Chat message and streaming UI state SHALL be managed with a Zustand store (`useChatStore`) separate from presentational components.

#### Scenario: Stream updates store

- **WHEN** AI SDK stream events update the active assistant message
- **THEN** UI reflects tokens without full page reload and remains consistent with API after `onFinish` refetch

### Requirement: Local web performance observability

The web application SHALL expose Core Web Vitals in local development and provide a script to audit chat page performance.

#### Scenario: Dev alert on poor vitals

- **WHEN** a Core Web Vital reports `needs-improvement` or `poor` in development
- **THEN** the Next dev server terminal logs `[WebVitals ⚠]` and the UI shows a dismissible corner hint without blocking interaction

#### Scenario: Verbose vitals logging

- **WHEN** `NEXT_PUBLIC_WEB_VITALS_VERBOSE=1` is set in development
- **THEN** all reported metrics are logged to the browser console with `[WebVitals]`

#### Scenario: Lighthouse chat audit

- **WHEN** developer runs `pnpm lighthouse:chat` with web dev server on port 3000
- **THEN** a performance HTML report is written under `apps/web/.lighthouse/`

### Requirement: RAG reference section in assistant Markdown

The chat UI SHALL render assistant messages that include a `## 参考来源` Markdown section with readable styling distinct from the main answer body.

#### Scenario: Reference section visible after stream

- **WHEN** assistant streaming completes and content includes `## 参考来源`
- **THEN** the reference block is displayed below the main answer with subdued typography or collapsible presentation

#### Scenario: Messages without references unchanged

- **WHEN** assistant content has no reference heading
- **THEN** message layout matches pre-RAG chat rendering

### Requirement: BFF forwards RAG sources via Data Stream

The web BFF chat route SHALL convert upstream SSE `sources` events into AI SDK Data Stream parts consumable by the chat UI before token text arrives.

#### Scenario: Sources part precedes text

- **WHEN** upstream SSE emits `sources` then `token` events for a RAG completion
- **THEN** the BFF response stream delivers a structured sources data part before the first text delta

#### Scenario: Token-only path unchanged

- **WHEN** upstream SSE emits only `token` and `done` without `sources`
- **THEN** the BFF still completes a valid data stream with text deltas only

### Requirement: Structured RAG citation chips in chat UI

The chat UI SHALL render assistant messages with structured RAG citation chips when sources are available from the stream or persisted message metadata.

#### Scenario: Chips during streaming

- **WHEN** assistant message is streaming and sources data part is received
- **THEN** citation chips appear below the in-progress answer before streaming completes

#### Scenario: Chips after reload

- **WHEN** user reloads conversation history and assistant message metadata contains `rag_sources`
- **THEN** citation chips render without parsing Markdown reference headings

#### Scenario: Cancel and regenerate unchanged layout

- **WHEN** user stops streaming or regenerates the latest assistant message
- **THEN** message list integrity and citation chip placement match pre-upgrade behavior aside from structured sources

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

