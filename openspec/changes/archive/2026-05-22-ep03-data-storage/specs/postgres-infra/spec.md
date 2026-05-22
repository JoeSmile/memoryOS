## ADDED Requirements

### Requirement: Local PostgreSQL via Docker Compose

The project SHALL provide a Docker Compose configuration that starts PostgreSQL 16 for local development with a documented default connection string.

#### Scenario: Developer starts database

- **WHEN** developer runs `docker compose up -d` from `infra/docker/`
- **THEN** PostgreSQL accepts connections on port 5432 with database `memoryos`

#### Scenario: Connection string documented

- **WHEN** developer reads `infra/docker/README.md` or `apps/api/.env.example`
- **THEN** they find `DATABASE_URL` example matching the Compose credentials

### Requirement: Database persistence across restarts

The Compose setup SHALL use a named volume so data persists across container restarts unless the volume is explicitly removed.

#### Scenario: Data survives container restart

- **WHEN** developer restarts the postgres container without removing the volume
- **THEN** previously created tables and rows remain available
