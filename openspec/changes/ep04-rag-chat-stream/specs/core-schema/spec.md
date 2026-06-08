## ADDED Requirements

### Requirement: Message metadata JSONB column

The schema SHALL provide a nullable `metadata` JSONB column on `messages` for extensible per-message attributes such as RAG source citations.

#### Scenario: Migration adds metadata

- **WHEN** developer runs `alembic upgrade head` after the metadata revision
- **THEN** the `messages` table contains a nullable `metadata` JSONB column

#### Scenario: Legacy messages unchanged

- **WHEN** messages existed before the metadata migration
- **THEN** their `metadata` column is null and APIs remain backward compatible
