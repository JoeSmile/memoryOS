# data-access-layer Specification

## Purpose
TBD - created by archiving change ep03-data-storage. Update Purpose after archive.
## Requirements
### Requirement: Async database session dependency

The API SHALL expose `Depends(get_db)` providing an async SQLAlchemy session per request with proper cleanup after the request completes.

#### Scenario: Route uses database session

- **WHEN** a v1 route declares `db: AsyncSession = Depends(get_db)`
- **THEN** the route can execute async queries within the request lifecycle without leaking connections

### Requirement: Alembic manages schema versions

Schema changes SHALL be applied via Alembic migrations; fresh environments SHALL reach current schema with `alembic upgrade head`.

#### Scenario: Fresh database migration

- **WHEN** developer runs `alembic upgrade head` against an empty database
- **THEN** tables `users`, `conversations`, and `messages` are created

### Requirement: Repository and service separation

Business routes SHALL NOT execute raw SQL; data access MUST go through Repository classes and business rules through Service classes.

#### Scenario: List conversations via service

- **WHEN** client calls `GET /api/v1/conversations` with valid `user_id`
- **THEN** the handler delegates to a Service that uses a Repository and returns unified `{ code, message, data }` JSON

### Requirement: Create conversation API

The API SHALL allow creating a conversation linked to a user with a title.

#### Scenario: Create conversation success

- **WHEN** client sends `POST /api/v1/conversations` with `user_id` and `title`
- **THEN** response returns `code` 0 and `data` containing the new conversation `id`

#### Scenario: List conversations for user

- **WHEN** client sends `GET /api/v1/conversations?user_id=<uuid>`
- **THEN** response returns `code` 0 and `data` as a list of conversations for that user

### Requirement: Configuration from environment

`DATABASE_URL` SHALL be loaded from environment via pydantic-settings with a documented example in `.env.example`.

#### Scenario: Missing database URL

- **WHEN** `DATABASE_URL` is unset in production-like mode
- **THEN** application startup or database module fails with a clear configuration error

