## ADDED Requirements

### Requirement: Production-ready API container image

The repository SHALL include a multi-stage Dockerfile for `apps/api` that installs dependencies, runs as a non-root user, and starts the FastAPI application with uvicorn on port 8000.

#### Scenario: API image builds successfully

- **WHEN** developer runs `docker build` against `apps/api/Dockerfile`
- **THEN** the build completes and the container exposes port 8000

#### Scenario: API container runs without root

- **WHEN** the API container starts
- **THEN** the main process does not run as UID 0

### Requirement: Production-ready web container image

The repository SHALL include a multi-stage Dockerfile for `apps/web` using Next.js standalone output suitable for containerized deployment.

#### Scenario: Web image builds successfully

- **WHEN** developer runs `docker build` against `apps/web/Dockerfile`
- **THEN** the build completes and the container serves the Next.js app on port 3000

#### Scenario: Standalone output includes static assets

- **WHEN** the web container serves pages built with standalone output
- **THEN** static assets and public files required by Next.js are present in the runtime image

### Requirement: Docker full-stack environment template

The project SHALL provide a documented example environment file for the Compose full profile listing required secrets and service URLs without committing real credentials.

#### Scenario: Docker full env template exists

- **WHEN** developer reads `infra/docker/.env.docker.full.example`
- **THEN** they see placeholders for JWT secret, database URL, Redis URL, LLM keys, and CORS origins suitable for local Compose networking

### Requirement: Local deployment documentation

The project SHALL maintain deployment documentation covering local full-stack startup, database migration inside Compose, and SSE smoke verification through Nginx.

#### Scenario: Developer follows local deployment guide

- **WHEN** developer reads `docs/tech/deployment.md`
- **THEN** they find steps for `docker compose --profile full`, Alembic migrate, documented ports, and SSE verification without cloud provider setup

### Requirement: Local Ollama LLM and embedding integration

The project SHALL support configuring chat LLM and embedding models against a local Ollama OpenAI-compatible API, with separate base URLs for chat and embeddings, while preserving mock mode when no API key is configured.

#### Scenario: Ollama preset documented

- **WHEN** developer reads `docs/tech/ollama-local.md` and the Ollama blocks in environment example files
- **THEN** they find install steps, recommended chat and embedding models, `host.docker.internal` networking for Compose, and re-ingest guidance when embedding dimensions change

#### Scenario: Embedding uses independent base URL

- **WHEN** `EMBEDDING_BASE_URL` is set to an Ollama endpoint and `OPENAI_API_KEY` is set for live mode
- **THEN** `EmbeddingService` calls the embedding base URL while chat uses `OPENAI_BASE_URL`

#### Scenario: Harness remains mock without API key

- **WHEN** CI or tests run without `OPENAI_API_KEY`
- **THEN** chat and embeddings continue to use deterministic mock behavior unchanged
