# rag-retrieval Specification

## Purpose

Authenticated vector similarity search API for ingested knowledge chunks (EP04 RAG first slice).

## Requirements

### Requirement: Knowledge search API

The API SHALL expose `POST /api/v1/knowledge/search` accepting a query string, optional collection filter, and `top_k`, returning ranked chunks with similarity scores.

#### Scenario: Search returns relevant chunks

- **WHEN** authenticated client posts a query after World Cup data is ingested
- **THEN** response envelope `code=0` includes `data.chunks` array ordered by descending similarity

#### Scenario: Collection filter

- **WHEN** client sets `collection` to `worldcup-matches`
- **THEN** all returned chunks belong to documents in that collection only

### Requirement: Mock embeddings for offline harness

When `OPENAI_API_KEY` is unset, embedding generation SHALL use a deterministic mock implementation so ingest and search work without external API calls.

#### Scenario: Harness without API key

- **WHEN** harness runs ingest and search with `openai_api_key` unset
- **THEN** requests succeed and return at least one chunk for a seeded query

### Requirement: Search requires authentication

Knowledge search SHALL require a valid JWT Bearer token consistent with other protected API routes.

#### Scenario: Unauthenticated search rejected

- **WHEN** client calls search without `Authorization` header
- **THEN** API returns HTTP 401 with envelope `code=40101`
