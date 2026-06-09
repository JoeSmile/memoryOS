## MODIFIED Requirements

### Requirement: SSE event envelope

Each SSE `data:` line SHALL be a JSON object with `event` and `data` fields.

#### Scenario: Token event shape

- **WHEN** model produces incremental text
- **THEN** a line is sent as `{"event":"token","data":{"content":"<string>"}}`

#### Scenario: Sources event for RAG chat

- **WHEN** chat completion uses RAG retrieval and qualifying knowledge chunks exist
- **THEN** a line is sent as `{"event":"sources","data":{"items":[...]}}` after `start` and before the first `token` event

#### Scenario: Done event includes sources for persistence

- **WHEN** a RAG chat stream completes successfully with qualifying sources
- **THEN** the final `done` event SHALL include `data.sources` mirroring the earlier `sources` event items and the persisted assistant message metadata

## ADDED Requirements

### Requirement: RAG sources persisted on assistant message

When a RAG chat completion finalizes with qualifying sources, the system SHALL persist those sources on the assistant message row metadata before the stream ends.

#### Scenario: Metadata written on finalize

- **WHEN** chat completion stream completes with `done.data.sources` containing at least one item
- **THEN** the persisted assistant message has `metadata.rag_sources` equal to that sources array

#### Scenario: No metadata when no sources

- **WHEN** chat completion completes with no qualifying RAG sources
- **THEN** the assistant message `metadata` is null or omits `rag_sources`

#### Scenario: List messages returns metadata

- **WHEN** client lists messages for a conversation
- **THEN** each message includes its `metadata` field for UI citation rendering
