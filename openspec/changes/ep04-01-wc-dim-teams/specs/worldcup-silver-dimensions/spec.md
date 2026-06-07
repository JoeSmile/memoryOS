# worldcup-silver-dimensions

Silver 层世界杯维度表与 Bronze CSV 加载。

## ADDED Requirements

### Requirement: Dimension tables exist via Alembic

The system SHALL provide migration `003_wc_dimension_tables` creating `wc_confederations`, `wc_teams`, `wc_tournaments`, and `wc_stadiums` with TEXT primary keys matching Bronze identifiers.

#### Scenario: Migration applies cleanly

- **WHEN** `alembic upgrade head` runs on an empty database after core migrations
- **THEN** all four `wc_*` dimension tables exist

### Requirement: Teams reference confederations

`wc_teams.confederation_id` SHALL be a foreign key to `wc_confederations.id`.

#### Scenario: Team FK constraint

- **WHEN** a team row is inserted with unknown `confederation_id`
- **THEN** the database rejects the insert

### Requirement: Tournament slug for API compatibility

`wc_tournaments` SHALL include a unique `slug` column derived from `tournament_id` (e.g. `WC-2022` → `wc2022`).

#### Scenario: Slug mapping

- **WHEN** `WC-2022` is loaded from `tournaments.csv`
- **THEN** the row has `slug` equal to `wc2022`

### Requirement: Dimension ETL upserts from Bronze

The system SHALL provide a dimension loader that upserts rows from the four Bronze CSV files in dependency order.

#### Scenario: Full dimension load

- **WHEN** the operator runs `run.py dimensions` against the project's Bronze directory
- **THEN** row counts match CSV rows: 6 confederations, 88 teams, 30 tournaments, 240 stadiums

#### Scenario: Idempotent reload

- **WHEN** dimension load runs twice without CSV changes
- **THEN** row counts remain unchanged and no duplicate primary keys exist

### Requirement: Wiki link cleaning

Loaders SHALL convert `not applicable` and empty wiki URL fields to SQL NULL.

#### Scenario: Teams wiki cleanup

- **WHEN** a team row has `womens_team_wikipedia_link` of `not applicable`
- **THEN** the stored value is NULL

### Requirement: Transform unit tests

Pure transform helpers (slug, wiki clean, boolean parse) SHALL have unit tests independent of PostgreSQL.

#### Scenario: Slug unit test

- **WHEN** `tournament_slug("WC-2022")` is called
- **THEN** it returns `wc2022`
