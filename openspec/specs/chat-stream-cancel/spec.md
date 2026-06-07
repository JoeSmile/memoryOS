# chat-stream-cancel Specification

## Purpose

Hybrid stop for EP02 streaming chat: HTTP abort plus `POST /api/v1/chat/completions/cancel`, interrupted assistant persistence aligned with UI snapshot.

## Requirements

### Requirement: Stream identity at stream start

The chat completions SSE stream SHALL expose a `stream_id` before or with the first token so clients can target cancel requests.

#### Scenario: Start event on connect

- **WHEN** an authenticated chat completions stream begins
- **THEN** the server emits `{"event":"start","data":{"stream_id":"<uuid>"}}` before or immediately around the first `token` event

### Requirement: Redis-backed cancel flag

The system SHALL support a cancel flag keyed by `stream_id` with TTL, checkable during token streaming across workers when Redis is available.

#### Scenario: Cancel API sets flag

- **WHEN** client posts a valid cancel request for an active `stream_id` they own
- **THEN** a cancel marker is stored and subsequent token loop iterations observe cancellation

#### Scenario: Idempotent cancel

- **WHEN** client repeats cancel for the same `stream_id` while `stream_active` still exists
- **THEN** response remains success without error

#### Scenario: Reject cancel without active owner

- **WHEN** `stream_active` is missing for `stream_id` even if cancel flag remains
- **THEN** response is HTTP 404

### Requirement: Chat completions cancel endpoint

The API SHALL expose `POST /api/v1/chat/completions/cancel` for authenticated users.

#### Scenario: Cancel owned active stream

- **WHEN** client sends `{ "stream_id": "<uuid>" }` with valid Bearer token for a stream they own
- **THEN** response is HTTP 200 with unified success envelope

#### Scenario: Cancel with visible snapshot

- **WHEN** client sends `visible_length` and optionally `visible_content` (≤256 chars, must match length when both present)
- **THEN** interrupted assistant persistence truncates to the UI snapshot on finalize

#### Scenario: Reject foreign stream

- **WHEN** `stream_id` is unknown or belongs to another user
- **THEN** response is HTTP 404 with business error before side effects

#### Scenario: Reject unauthenticated cancel

- **WHEN** Authorization is missing or invalid
- **THEN** response is HTTP 401

### Requirement: Upstream LLM teardown on cancel or disconnect

The system SHALL stop consuming the LangChain/OpenAI streaming HTTP response when the client disconnects or the cancel flag is set.

#### Scenario: Disconnect stops upstream read

- **WHEN** HTTP client disconnects mid-stream
- **THEN** the runner stops yielding new tokens and closes the upstream stream handle in a `finally` path

#### Scenario: Cancel API stops upstream read

- **WHEN** cancel flag is set while stream is active
- **THEN** the token loop exits and upstream stream handle is closed without emitting further tokens

### Requirement: Frontend hybrid stop

The web client SHALL combine connection abort with a cancel API call when stopping generation.

#### Scenario: Stop aborts fetch and calls cancel

- **WHEN** user clicks stop during an active stream with known `stream_id`
- **THEN** the client freezes visible assistant text, aborts the in-flight chat request, and issues a non-blocking cancel API request with `visible_length` (and inline `visible_content` when ≤256 chars)
