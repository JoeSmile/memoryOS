## ADDED Requirements

### Requirement: Local Redis via Docker Compose

The project SHALL provide a Docker Compose `redis` service using Redis 7 Alpine for local development with a documented default `REDIS_URL`.

#### Scenario: Developer starts Redis

- **WHEN** developer runs `docker compose up -d` from `infra/docker/`
- **THEN** Redis accepts connections on port 6379

#### Scenario: Connection string documented

- **WHEN** developer reads `infra/docker/README.md` or `apps/api/.env.example`
- **THEN** they find `REDIS_URL=redis://localhost:6379/0` matching the Compose service

### Requirement: Redis persistence across restarts

The Compose setup SHALL use a named volume `redis-data` so data persists across container restarts unless the volume is explicitly removed.

#### Scenario: Data survives container restart

- **WHEN** developer restarts the redis container without removing the volume
- **THEN** previously stored keys remain available until TTL expires

### Requirement: Async Redis client configuration

The API SHALL load `REDIS_URL` from environment via pydantic-settings and expose an async Redis client for application code.

#### Scenario: Redis URL configured

- **WHEN** `REDIS_URL` is set to a valid redis URL
- **THEN** application code can obtain a shared async Redis connection

#### Scenario: Redis URL unset

- **WHEN** `REDIS_URL` is not configured
- **THEN** cache features are disabled without preventing API startup

### Requirement: Health reports Redis status

Health endpoints SHALL include a `redis` field in `data` with value `ok`, `down`, or `disabled`.

#### Scenario: Redis healthy

- **WHEN** `REDIS_URL` is configured and Redis responds to PING
- **THEN** health `data.redis` is `ok`

#### Scenario: Redis unavailable

- **WHEN** `REDIS_URL` is configured but Redis does not respond
- **THEN** health `data.redis` is `down` and overall `data.status` remains `ok` for the API process
