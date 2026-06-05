## ADDED Requirements

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
