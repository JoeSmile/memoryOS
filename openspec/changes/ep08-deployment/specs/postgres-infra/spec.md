## ADDED Requirements

### Requirement: Full-stack Compose profile

The project SHALL provide a Docker Compose profile that runs web, API, PostgreSQL, Redis, and Nginx together while preserving the default Compose behavior of starting only PostgreSQL and Redis for local development.

#### Scenario: Default compose unchanged for dev DB

- **WHEN** developer runs `docker compose up -d` without profiles from `infra/docker/`
- **THEN** only PostgreSQL and Redis start as today

#### Scenario: Full profile starts application stack

- **WHEN** developer runs Compose with the documented full profile
- **THEN** web, api, nginx, postgres, and redis services start with healthchecks and service DNS names suitable for inter-container networking

### Requirement: Nginx SSE proxy configuration

The deployment stack SHALL include Nginx configuration that disables response buffering and uses appropriate timeouts for Server-Sent Events chat streaming to the API.

#### Scenario: SSE location disables buffering

- **WHEN** Nginx proxies chat completion SSE requests to the API
- **THEN** `proxy_buffering` is off and read/send timeouts support long-lived streams

#### Scenario: API and web routed through Nginx

- **WHEN** client accesses the documented local full-stack entry URL (e.g. nginx mapped port)
- **THEN** browser requests to web pages and `/api/v1/` routes reach the correct upstream containers

## MODIFIED Requirements

### Requirement: Local PostgreSQL via Docker Compose

The project SHALL provide Docker Compose configuration for local PostgreSQL 16 with pgvector and Redis 7, and SHALL document how to optionally extend the same compose file with a full application stack profile.

#### Scenario: Developer starts database stack

- **WHEN** developer runs `docker compose up -d` from `infra/docker/` without profiles
- **THEN** PostgreSQL accepts connections on port 5432 with `CREATE EXTENSION vector` available, and Redis on port 6379

#### Scenario: Connection string documented

- **WHEN** developer reads `infra/docker/README.md` or `apps/api/.env.example`
- **THEN** they find `DATABASE_URL` and `REDIS_URL` examples matching the Compose credentials

#### Scenario: Full stack connection strings use service names

- **WHEN** API runs inside the full Compose profile
- **THEN** documented environment examples use `postgres` and `redis` hostnames instead of `localhost`
