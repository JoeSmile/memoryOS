## ADDED Requirements

### Requirement: Redis URL configuration

`REDIS_URL` SHALL be loaded from environment via pydantic-settings with a documented example in `.env.example`. Cache behavior SHALL be skipped when unset.

#### Scenario: Redis configured for caching

- **WHEN** `REDIS_URL` is set and Redis is reachable
- **THEN** conversation list reads MAY use Redis cache per Cache-Aside rules

### Requirement: Conversation list uses cache when available

`GET /api/v1/conversations` SHALL delegate to `ConversationService` which attempts Redis cache before PostgreSQL when Redis is enabled.

#### Scenario: List conversations with cache

- **WHEN** client sends `GET /api/v1/conversations?user_id=<uuid>` and cache is warm
- **THEN** response returns `code` 0 and `data` as the same conversation list schema as a database read
