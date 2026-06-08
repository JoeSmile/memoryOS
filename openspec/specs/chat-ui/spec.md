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

