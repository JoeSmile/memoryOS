# chat-sse Specification

## Purpose

SSE streaming chat completions for EP02: authenticated users send messages and receive token-level assistant output via `POST /api/v1/chat/completions`.
## Requirements
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

### Requirement: SSE event envelope

Each SSE `data:` line SHALL be a JSON object with `event` and `data` fields.

#### Scenario: Token event shape

- **WHEN** model produces incremental text
- **THEN** a line is sent as `{"event":"token","data":{"content":"<string>"}}`

#### Scenario: Sources event for RAG chat

- **WHEN** chat completion uses RAG retrieval and qualifying knowledge chunks exist
- **THEN** a line is sent as `{"event":"sources","data":{"items":[...]}}` after `start` and before the first `token` event

#### Scenario: Done event may include sources summary

- **WHEN** a RAG chat stream completes successfully with qualifying sources
- **THEN** the final `done` event MAY include `data.sources` mirroring the earlier `sources` event items for client binding to `message_id`

### Requirement: User message persistence before stream

The system SHALL persist the user message to PostgreSQL before emitting assistant tokens, except when `regenerate` is true.

#### Scenario: User message saved

- **WHEN** chat completions request is accepted with `regenerate` false or omitted
- **THEN** a `messages` row with role `user` exists for the conversation before first `token` event

#### Scenario: Regenerate skips new user row

- **WHEN** chat completions request has `regenerate: true`
- **THEN** no additional user message row is inserted for that request

### Requirement: Mock stream without API key

When `OPENAI_API_KEY` is unset, the system SHALL still produce a valid SSE stream for development and tests.

#### Scenario: Harness mock stream

- **WHEN** chat completions is called in test environment without OpenAI credentials
- **THEN** SSE completes with `done` and deterministic token content without external network

### Requirement: Client disconnect cancels upstream

The system SHALL stop reading the model stream and close upstream LLM HTTP when the HTTP client disconnects or when a stream cancel flag is set.

#### Scenario: Disconnect during stream

- **WHEN** client closes connection mid-stream
- **THEN** upstream consumption stops, the upstream stream handle is closed, and partial stream cache key is cleared or left to TTL

#### Scenario: Cancel flag during stream

- **WHEN** cancel marker is set for the active `stream_id`
- **THEN** upstream consumption stops without waiting for another client disconnect

