# redis-cache Specification

## Purpose

Cache-Aside conversation list and stream temporary buffer for EP02/EP03 (Story 3.3).

## Requirements

### Requirement: Conversation list cache with Cache-Aside

The system SHALL cache each user's conversation list in Redis using key `memoryos:conversations:user:{user_id}` with TTL 300 seconds, storing JSON serialized conversation DTOs.

#### Scenario: Cache miss loads database

- **WHEN** client calls `GET /api/v1/conversations` and no cache entry exists for the user
- **THEN** the service loads conversations from PostgreSQL and populates the cache

#### Scenario: Cache hit avoids database list query

- **WHEN** client calls `GET /api/v1/conversations` and a valid cache entry exists
- **THEN** the service returns cached data without querying PostgreSQL for the list

#### Scenario: Create conversation invalidates cache

- **WHEN** client successfully creates a conversation via `POST /api/v1/conversations` and the database transaction commits
- **THEN** the user's conversation list cache key is deleted before the response is returned

### Requirement: Stream temporary cache for EP02

The system SHALL provide a stream cache abstraction using keys `memoryos:stream:{conversation_id}:{stream_id}` with TTL 3600 seconds for partial SSE content.

#### Scenario: Append stream chunk

- **WHEN** application calls stream cache append with conversation id, stream id, and text chunk
- **THEN** Redis stores the accumulated content with refreshed TTL

#### Scenario: Read stream buffer

- **WHEN** application calls stream cache get for an existing stream key
- **THEN** the full accumulated text is returned

#### Scenario: Clear stream buffer

- **WHEN** application calls stream cache delete for a stream key
- **THEN** the key is removed from Redis
