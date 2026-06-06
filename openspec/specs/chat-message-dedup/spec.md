# chat-message-dedup Specification

## Purpose

Send idempotency and regenerate semantics for EP02 chat: `client_message_id` deduplication, interrupted assistant persistence, and frontend send guards.

## Requirements

### Requirement: Client message idempotency key

The system SHALL accept an optional `client_message_id` (UUID) on chat completion requests to deduplicate user message persistence per conversation.

#### Scenario: First send with client message id

- **WHEN** client posts chat completion with unique `client_message_id` for the conversation
- **THEN** exactly one `messages` row with role `user` is created carrying that `client_message_id`

#### Scenario: Duplicate client message id with completed turn

- **WHEN** client repeats the same `client_message_id` and a **completed** assistant message exists for that user turn
- **THEN** API rejects before SSE with a business error indicating duplicate message

#### Scenario: Duplicate client message id with interrupted or missing assistant

- **WHEN** client repeats the same `client_message_id` and no assistant exists, or only an **interrupted** partial assistant exists
- **THEN** API reuses the existing user row, removes any interrupted partial assistant if present, and streams a new assistant reply

### Requirement: Persist partial assistant on stream interrupt

When the client disconnects mid-stream (stop, abort, or close), the system SHALL persist buffered assistant text when non-empty.

#### Scenario: Stop with partial tokens

- **WHEN** HTTP client disconnects after at least one assistant token was produced
- **THEN** an assistant message row is saved with the buffered content and `completion_status` interrupted

#### Scenario: Stop with no tokens

- **WHEN** HTTP client disconnects before any assistant token
- **THEN** no assistant message row is created

### Requirement: Regenerate without duplicate user turn

The system SHALL support `regenerate: true` to replace the latest assistant reply without inserting a new user message.

#### Scenario: Regenerate latest assistant

- **WHEN** client posts chat completion with `regenerate: true` for a conversation that has at least one user message
- **THEN** no new user message row is created, the previous latest assistant message is removed if present, and a new assistant stream is produced

### Requirement: Frontend send guard

The web client SHALL prevent concurrent duplicate sends from the composer while a send is in flight.

#### Scenario: Double submit blocked

- **WHEN** user triggers submit twice before streaming status activates
- **THEN** at most one completion request is initiated
