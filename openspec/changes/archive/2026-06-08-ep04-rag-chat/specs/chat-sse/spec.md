## MODIFIED Requirements

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
