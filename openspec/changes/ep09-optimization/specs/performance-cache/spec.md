# performance-cache Specification

## Purpose

Caching and database performance improvements (EP09 Story 9.2).

## Requirements

### Requirement: Embedding result cache

When `EMBEDDING_CACHE_ENABLED` is true, the embedding service SHALL cache vector results in Redis keyed by normalized input text hash with configurable TTL.

#### Scenario: Cache hit avoids provider call

- **WHEN** identical normalized text is embedded twice within TTL
- **THEN** second call returns cached vector without external API request

#### Scenario: Cache miss stores result

- **WHEN** text is embedded for the first time
- **THEN** result is stored in Redis with TTL

### Requirement: Database index review for hot paths

Conversation message listing and token usage aggregation queries SHALL use indexes documented in migration or `docs/tech/`.

#### Scenario: Messages by conversation indexed

- **WHEN** migration for EP09 is applied
- **THEN** `messages(conversation_id, created_at)` or equivalent index exists for list-by-conversation queries

#### Scenario: Token usage by user and day indexed

- **WHEN** token usage table exists
- **THEN** composite index supports daily aggregation by `user_id` and date

### Requirement: Time to first token observability

The API SHALL expose phase or start timestamps sufficient to measure retrieve duration in logs or tracing without blocking the stream.

#### Scenario: Retrieve duration logged

- **WHEN** a chat completion includes RAG retrieve
- **THEN** structured log or trace span records retrieve elapsed milliseconds
