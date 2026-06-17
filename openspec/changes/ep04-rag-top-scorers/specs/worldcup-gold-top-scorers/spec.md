# worldcup-gold-top-scorers

## Purpose

Generate per-tournament top-scorer ranking fact cards from Silver `wc_goals` for EP04 RAG retrieval (aggregate list queries).

## ADDED Requirements

### Requirement: Tournament top scorers JSONL export

The system SHALL aggregate non-own-goal counts from `wc_goals` per tournament and player, rank players by goals descending, and export one fact card per tournament to `data/gold/worldcup/fact_cards/tournament_scorers.jsonl`.

Each line MUST be a JSON object with keys: `id`, `entity_type`, `source_ids`, `text`.

- `entity_type` MUST be `tournament_scorers`
- `id` MUST be `tournament_scorers:{tournament_id}` (e.g. `tournament_scorers:WC-2022`)
- `source_ids` MUST include the tournament id and each ranked player's id

#### Scenario: WC-2022 card lists top 10

- **WHEN** fact card export runs with Silver populated and default top-N=10
- **THEN** `tournament_scorers.jsonl` contains a line for `WC-2022` whose `text` lists at least 10 ranked players with goal counts
- **AND** rank 1 names Kylian Mbappé with 8 goals

#### Scenario: Tournament filter

- **WHEN** export runs with `--tournament WC-2022`
- **THEN** only the WC-2022 tournament scorers card is written to the filtered output set

#### Scenario: Own goals excluded

- **WHEN** a goal row has `own_goal=true`
- **THEN** that goal is not counted toward any player's tournament total in the ranking text

### Requirement: Traceable source_ids on scorers card

Each tournament scorers card MUST include `source_ids` containing the tournament primary key and every ranked player's Silver id appearing in the card text.

#### Scenario: Player ids in source_ids

- **WHEN** the WC-2022 scorers card is generated
- **THEN** `source_ids` includes `WC-2022`, `P-64077` (Mbappé), and `P-14758` (Messi)

### Requirement: Ingest support for tournament_scorers collection

The knowledge ingest pipeline SHALL treat `tournament_scorers.jsonl` as a default Gold stem, mapping to collection `worldcup-tournament_scorers`.

#### Scenario: Default ingest includes scorers stem

- **WHEN** ingest runs without `--collections` override
- **THEN** documents from `tournament_scorers.jsonl` are embedded into `worldcup-tournament_scorers`

#### Scenario: Search retrieves scorers card for ranking query

- **WHEN** World Cup data is ingested including tournament scorers cards
- **AND** client searches with query `2022世界杯射手榜前10名`
- **THEN** at least one of the top 3 results has `external_id` `tournament_scorers:WC-2022`
