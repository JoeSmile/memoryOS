## ADDED Requirements

### Requirement: Composite indexes for list queries

Schema migration SHALL add indexes optimized for listing conversations by user ordered by recency and messages by conversation ordered by time.

#### Scenario: Migration applies indexes

- **WHEN** developer runs `alembic upgrade head` after revision 002
- **THEN** PostgreSQL contains composite indexes documented in `docs/database.md` for conversation and message list patterns
