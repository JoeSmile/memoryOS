# worldcup-gold-fact-cards

## Purpose

Export human-readable fact cards from Silver PostgreSQL for EP04 RAG ingestion.

## Requirements

### Requirement: JSONL export per entity type

The system SHALL write `matches.jsonl`, `players.jsonl`, and `tournaments.jsonl` under `data/gold/worldcup/fact_cards/`.

Each line MUST be a JSON object with keys: `id`, `entity_type`, `source_ids`, `text`.

#### Scenario: Full export

- **WHEN** `fact_cards.py` runs without `--tournament`
- **THEN** all Silver matches, players, and tournaments are exported

#### Scenario: Tournament filter

- **WHEN** `--tournament WC-2022` is passed
- **THEN** only that tournament's matches and tournament card are exported; players limited to squad members

### Requirement: Traceable source_ids

Each card MUST include at least one Silver primary key in `source_ids` (e.g. `M-2022-64`, `P-03484`, `WC-2022`).

#### Scenario: Match card sources

- **WHEN** a match card is generated
- **THEN** `source_ids` contains the match id and tournament id

### Requirement: Spotlight samples

The system SHALL write `samples.jsonl` with exactly 10 curated cards for manual spot-check.

#### Scenario: Sample count

- **WHEN** export completes
- **THEN** `samples.jsonl` has 10 lines including WC-2022 final match card
