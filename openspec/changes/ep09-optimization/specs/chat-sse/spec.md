# chat-sse Specification (Delta)

## ADDED Requirements

### Requirement: Phase SSE event

The chat completion SSE stream SHALL emit `phase` events to indicate retrieve, model, or tool preparation stages before tokens.

#### Scenario: Phase event shape

- **WHEN** runner enters retrieve stage
- **THEN** a line is sent as `{"event":"phase","data":{"id":"retrieve","label":"<string>"}}`

#### Scenario: Phase before sources and tokens

- **WHEN** RAG completion runs successfully
- **THEN** at least one `phase` event is emitted after `start` and before the first `token` event

#### Scenario: Phase disabled by configuration

- **WHEN** `AGENT_PHASE_EVENTS_ENABLED` is false
- **THEN** stream omits `phase` events but still emits `start`, optional `sources`, and `token` events
