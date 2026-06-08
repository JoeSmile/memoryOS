## ADDED Requirements

### Requirement: BFF forwards RAG sources via Data Stream

The web BFF chat route SHALL convert upstream SSE `sources` events into AI SDK Data Stream parts consumable by the chat UI before token text arrives.

#### Scenario: Sources part precedes text

- **WHEN** upstream SSE emits `sources` then `token` events for a RAG completion
- **THEN** the BFF response stream delivers a structured sources data part before the first text delta

#### Scenario: Token-only path unchanged

- **WHEN** upstream SSE emits only `token` and `done` without `sources`
- **THEN** the BFF still completes a valid data stream with text deltas only

### Requirement: Structured RAG citation chips in chat UI

The chat UI SHALL render assistant messages with structured RAG citation chips when sources are available from the stream or persisted message metadata.

#### Scenario: Chips during streaming

- **WHEN** assistant message is streaming and sources data part is received
- **THEN** citation chips appear below the in-progress answer before streaming completes

#### Scenario: Chips after reload

- **WHEN** user reloads conversation history and assistant message metadata contains `rag_sources`
- **THEN** citation chips render without parsing Markdown reference headings

#### Scenario: Cancel and regenerate unchanged layout

- **WHEN** user stops streaming or regenerates the latest assistant message
- **THEN** message list integrity and citation chip placement match pre-upgrade behavior aside from structured sources
