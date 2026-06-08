# rag-ingest Specification

## Purpose

World Cup Gold JSONL ingest pipeline: CLI and service layer mapping fact cards to documents and chunks with idempotent upsert.

## Requirements

### Requirement: World Cup JSONL ingest

The system SHALL ingest all Gold fact card files under `data/gold/worldcup/fact_cards/*.jsonl` into `documents` and `document_chunks`, mapping each file stem to collection `worldcup-{stem}`.

#### Scenario: Default full Gold ingest

- **WHEN** ingest runs with no collection filter
- **THEN** documents exist for `matches`, `players`, `player_careers`, `tournaments`, and `samples` with line counts matching each JSONL file

#### Scenario: Ingest single collection

- **WHEN** ingest runs for collection stem `matches`
- **THEN** one document and one chunk exist per JSONL line with `external_id` equal to the line `id` field

### Requirement: Idempotent re-ingest

Re-running ingest for the same collection SHALL update existing documents and replace embeddings without creating duplicate documents.

#### Scenario: Second ingest same collection

- **WHEN** ingest runs twice for `player_careers` without data changes
- **THEN** document count for that collection remains equal to JSONL line count

### Requirement: CLI ingest entrypoint

A CLI command SHALL trigger World Cup ingest without requiring the HTTP server.

#### Scenario: CLI success

- **WHEN** developer runs `ingest_worldcup.py` with default collections
- **THEN** process exits 0 and prints ingested document counts per collection
