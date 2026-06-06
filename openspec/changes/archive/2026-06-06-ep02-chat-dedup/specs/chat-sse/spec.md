## MODIFIED Requirements

### Requirement: Chat completions SSE endpoint

The API SHALL expose `POST /api/v1/chat/completions` that returns `text/event-stream` for authenticated users.

#### Scenario: Stream tokens on valid request

- **WHEN** client sends valid Bearer token and body `{ conversation_id, content }` for a conversation owned by the user
- **THEN** response has `Content-Type` text/event-stream and emits at least one `token` event followed by a `done` event

#### Scenario: Stream with optional idempotency fields

- **WHEN** client includes optional `client_message_id` and/or `regenerate` in the request body
- **THEN** the server applies chat message deduplication and regenerate rules before streaming

#### Scenario: Reject unauthenticated request

- **WHEN** Authorization header is missing or invalid
- **THEN** response returns HTTP 401 with unified error envelope before SSE starts

#### Scenario: Reject foreign conversation

- **WHEN** conversation_id belongs to another user
- **THEN** response returns non-2xx with business error before SSE starts

### Requirement: User message persistence before stream

The system SHALL persist the user message to PostgreSQL before emitting assistant tokens, except when `regenerate` is true.

#### Scenario: User message saved

- **WHEN** chat completions request is accepted with `regenerate` false or omitted
- **THEN** a `messages` row with role `user` exists for the conversation before first `token` event

#### Scenario: Regenerate skips new user row

- **WHEN** chat completions request has `regenerate: true`
- **THEN** no additional user message row is inserted for that request
