## ADDED Requirements

### Requirement: Create conversation with first message in one transaction

The service layer SHALL support creating a conversation and its first message within a single database transaction committed by the route handler.

#### Scenario: Atomic create

- **WHEN** client invokes the combined create API or service method with valid user and message content
- **THEN** both conversation and message rows exist after commit, or neither exists after rollback

### Requirement: Configurable connection pool

SQLAlchemy async engine SHALL read pool size settings from environment with documented defaults in `.env.example`.

#### Scenario: Pool settings applied

- **WHEN** `DB_POOL_SIZE` is set
- **THEN** engine is created with matching pool configuration
