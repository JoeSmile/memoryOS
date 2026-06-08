## ADDED Requirements

### Requirement: RAG sources persisted with assistant message

When RAG chat completes with qualifying retrieval hits, the system SHALL store structured source items on the assistant message for reload and audit.

#### Scenario: Sources in message metadata after stream

- **WHEN** harness completes a RAG chat stream with sources events
- **THEN** fetching the assistant message by conversation list returns `metadata.rag_sources` with matching `external_id` values

#### Scenario: Mock path without external API

- **WHEN** harness runs RAG chat without `OPENAI_API_KEY` after ingesting samples
- **THEN** persisted assistant message metadata includes at least one rag source item
