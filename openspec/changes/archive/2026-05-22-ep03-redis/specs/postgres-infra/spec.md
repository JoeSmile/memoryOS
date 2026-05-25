## MODIFIED Requirements

### Requirement: Local PostgreSQL via Docker Compose

The project SHALL provide a Docker Compose configuration that starts PostgreSQL 16 and Redis 7 for local development with documented default connection strings.

#### Scenario: Developer starts database stack

- **WHEN** developer runs `docker compose up -d` from `infra/docker/`
- **THEN** PostgreSQL accepts connections on port 5432 and Redis on port 6379

#### Scenario: Connection string documented

- **WHEN** developer reads `infra/docker/README.md` or `apps/api/.env.example`
- **THEN** they find `DATABASE_URL` and `REDIS_URL` examples matching the Compose credentials

### Requirement: Database persistence across restarts

The Compose setup SHALL use named volumes so data persists across container restarts unless volumes are explicitly removed.

#### Scenario: Data survives container restart

- **WHEN** developer restarts postgres or redis containers without removing volumes
- **THEN** previously created PostgreSQL rows and Redis keys (within TTL) remain available
