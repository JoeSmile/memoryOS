## ADDED Requirements

### Requirement: Chat completions SSE endpoint

The API SHALL expose `POST /api/v1/chat/completions` that returns `text/event-stream` for authenticated users.

#### Scenario: Stream tokens on valid request

- **WHEN** client sends valid Bearer token and body `{ conversation_id, content }` for a conversation owned by the user
- **THEN** response has `Content-Type` text/event-stream and emits at least one `token` event followed by a `done` event

#### Scenario: Reject unauthenticated request

- **WHEN** Authorization header is missing or invalid
- **THEN** response returns HTTP 401 with unified error envelope before SSE starts

#### Scenario: Reject foreign conversation

- **WHEN** conversation_id belongs to another user
- **THEN** response returns non-2xx with business error before SSE starts

### Requirement: SSE event envelope

Each SSE `data:` line SHALL be a JSON object with `event` and `data` fields.

#### Scenario: Token event shape

- **WHEN** model produces incremental text
- **THEN** a line is sent as `{"event":"token","data":{"content":"<string>"}}`

#### Scenario: Done event shape

- **WHEN** stream completes successfully
- **THEN** a line is sent as `{"event":"done","data":{"message_id":"<uuid>","stream_id":"<uuid>"}}` and assistant message is persisted

### Requirement: User message persistence before stream

The system SHALL persist the user message to PostgreSQL before emitting assistant tokens.

#### Scenario: User message saved

- **WHEN** chat completions request is accepted
- **THEN** a `messages` row with role `user` exists for the conversation before first `token` event

### Requirement: Mock stream without API key

When `OPENAI_API_KEY` is unset, the system SHALL still produce a valid SSE stream for development and tests.

#### Scenario: Harness mock stream

- **WHEN** chat completions is called in test environment without OpenAI credentials
- **THEN** SSE completes with `done` and deterministic token content without external network

### Requirement: Client disconnect cancels upstream

The system SHALL stop reading the model stream when the HTTP client disconnects.

#### Scenario: Disconnect during stream

- **WHEN** client closes connection mid-stream
- **THEN** upstream consumption stops and partial stream cache key is cleared or left to TTL
