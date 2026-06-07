## MODIFIED Requirements

### Requirement: SSE event envelope

Each SSE `data:` line SHALL be a JSON object with `event` and `data` fields.

#### Scenario: Token event shape

- **WHEN** model produces incremental text
- **THEN** a line is sent as `{"event":"token","data":{"content":"<string>"}}`

#### Scenario: Start event shape

- **WHEN** stream begins for an authenticated completion
- **THEN** a line is sent as `{"event":"start","data":{"stream_id":"<uuid>"}}`

#### Scenario: Done event shape

- **WHEN** stream completes successfully
- **THEN** a line is sent as `{"event":"done","data":{"message_id":"<uuid>","stream_id":"<uuid>"}}` and assistant message is persisted

### Requirement: Client disconnect cancels upstream

The system SHALL stop reading the model stream and close upstream LLM HTTP when the HTTP client disconnects or when a stream cancel flag is set.

#### Scenario: Disconnect during stream

- **WHEN** client closes connection mid-stream
- **THEN** upstream consumption stops, the upstream stream handle is closed, and partial stream cache key is cleared or left to TTL

#### Scenario: Cancel flag during stream

- **WHEN** cancel marker is set for the active `stream_id`
- **THEN** upstream consumption stops without waiting for another client disconnect
