## ADDED Requirements

### Requirement: Production-ready API container image

The repository SHALL include a multi-stage Dockerfile for `apps/api` that installs dependencies, runs as a non-root user, and starts the FastAPI application with uvicorn on port 8000. The same Dockerfile SHALL be used for local builds and cloud deployment.

#### Scenario: API image builds successfully

- **WHEN** developer or CI runs `docker build` against `apps/api/Dockerfile`
- **THEN** the build completes and the container exposes port 8000

#### Scenario: API container runs without root

- **WHEN** the API container starts
- **THEN** the main process does not run as UID 0

### Requirement: Production-ready web container image

The repository SHALL include a multi-stage Dockerfile for `apps/web` using Next.js standalone output. The same Dockerfile SHALL be used for local builds and cloud deployment.

#### Scenario: Web image builds successfully

- **WHEN** developer or CI runs `docker build` against `apps/web/Dockerfile`
- **THEN** the build completes and the container serves the Next.js app on port 3000

#### Scenario: Standalone output includes static assets

- **WHEN** the web container serves pages built with standalone output
- **THEN** static assets and public files required by Next.js are present in the runtime image

### Requirement: Deployment environment contract

The project SHALL provide a documented deployment environment example defining a single set of variable keys with documented values for **local** and **cloud** profiles, without committing real credentials.

#### Scenario: Deployment env contract exists

- **WHEN** operator reads `infra/docker/.env.deployment.example`
- **THEN** they see the same keys for JWT, database, Redis, LLM, embedding, and CORS with commented local (Compose service names, Ollama) and cloud (managed services, API keys) value examples

#### Scenario: Compose uses configurable image tags

- **WHEN** operator sets `WEB_IMAGE` and `API_IMAGE` in deployment env
- **THEN** Compose full profile uses those tags so locally built images can be pushed and pulled on cloud hosts without rebuilding different images

### Requirement: Deployment documentation with promotion path

The project SHALL maintain deployment documentation covering local full-stack verification and a documented promotion path to cloud using the same images and environment keys.

#### Scenario: Local verification guide

- **WHEN** developer reads `docs/tech/deployment.md`
- **THEN** they find local `docker compose --profile full` smoke steps including migrate and SSE verification

#### Scenario: Cloud promotion guide

- **WHEN** operator reads `docs/tech/deployment.md`
- **THEN** they find steps to push images to a registry, apply cloud profile environment values, and run the same stack on a cloud host or hand off to K8s (EP14)

### Requirement: Local Ollama LLM and embedding integration

The project SHALL support configuring chat LLM and embedding models against a local Ollama OpenAI-compatible API under the **local** deployment profile, with separate base URLs for chat and embeddings, while preserving mock mode when no API key is configured.

#### Scenario: Ollama local profile documented

- **WHEN** developer reads `docs/tech/ollama-local.md` and the local section of deployment env examples
- **THEN** they find `qwen3:8b` chat and `mxbai-embed-large` embedding guidance, `host.docker.internal` networking, and re-ingest notes

#### Scenario: Embedding uses independent base URL

- **WHEN** `EMBEDDING_BASE_URL` is set and `OPENAI_API_KEY` enables live mode
- **THEN** `EmbeddingService` calls the embedding base URL while chat uses `OPENAI_BASE_URL`

#### Scenario: Harness remains mock without API key

- **WHEN** CI or tests run without `OPENAI_API_KEY`
- **THEN** chat and embeddings continue to use deterministic mock behavior unchanged

### Requirement: Deployment CI image build

CI SHALL build API and web Docker images on pull requests using the same Dockerfiles as local development.

#### Scenario: PR validates Docker builds

- **WHEN** a pull request modifies application or Docker-related paths
- **THEN** the deployment workflow runs `docker build` for web and api images and fails on build errors
