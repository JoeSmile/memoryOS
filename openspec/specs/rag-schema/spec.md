# rag-schema Specification

## Purpose

pgvector-backed RAG storage for EP04: `documents` and `document_chunks` tables with fixed-dimension embeddings.

## Requirements

### Requirement: pgvector extension enabled

PostgreSQL migrations SHALL enable the `vector` extension before creating embedding columns.

#### Scenario: Migration applies extension

- **WHEN** developer runs `alembic upgrade head` through revision `011`
- **THEN** `SELECT * FROM pg_extension WHERE extname = 'vector'` returns one row

### Requirement: Documents table for knowledge sources

The schema SHALL provide a `documents` table keyed by `(collection, external_id)` with metadata for RAG provenance.

#### Scenario: Document uniqueness per collection

- **WHEN** two rows share the same `collection` and `external_id`
- **THEN** the database rejects the duplicate per unique constraint

### Requirement: Document chunks with embeddings

The schema SHALL provide a `document_chunks` table storing chunk text and a fixed-dimension `vector` embedding linked to `documents` with cascade delete.

#### Scenario: Chunks removed with document

- **WHEN** a document row is deleted
- **THEN** all associated `document_chunks` rows are removed
