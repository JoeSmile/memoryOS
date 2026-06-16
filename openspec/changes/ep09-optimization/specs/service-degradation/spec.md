# service-degradation Specification

## Purpose

Graceful degradation when LLM, Redis, or vector retrieval fail (EP09 Story 9.5).

## Requirements

### Requirement: LLM primary with fallback model

When primary LLM invocation fails with retryable errors, the chat service SHALL attempt a configured fallback model before returning a terminal stream error.

#### Scenario: Primary fails fallback succeeds

- **WHEN** primary model returns timeout or 5xx and `LLM_FALLBACK_MODEL` is configured
- **THEN** completion retries with fallback and stream completes with assistant content

#### Scenario: Both models fail

- **WHEN** primary and fallback both fail
- **THEN** stream emits `error` event and assistant message is not marked complete

### Requirement: Vector retrieval degradation

When vector search fails or times out, the graph SHALL continue with empty retrieved chunks and `rag_sufficient=false` rather than failing the entire request.

#### Scenario: Retrieval timeout continues chat

- **WHEN** retrieve step exceeds configured timeout
- **THEN** runner logs degradation, emits optional phase event, and call_model proceeds without RAG chunks

### Requirement: Redis unavailable for cache and rate limit

When Redis is unavailable, optional cache and rate-limit features SHALL degrade without blocking core chat persistence in PostgreSQL.

#### Scenario: Chat works without Redis

- **WHEN** Redis is down and fail-open policies are enabled
- **THEN** authenticated user can still complete a chat turn persisted to PostgreSQL
