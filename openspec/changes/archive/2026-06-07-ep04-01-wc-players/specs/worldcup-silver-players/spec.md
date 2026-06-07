# worldcup-silver-players

Silver 层球员维度与参赛年份桥表。

## ADDED Requirements

### Requirement: Player tables via Alembic

The system SHALL provide migration `004_wc_players` creating `wc_players` and `wc_player_tournament_years`.

#### Scenario: Migration applies

- **WHEN** `alembic upgrade head` runs after `003`
- **THEN** both tables exist with FK `wc_player_tournament_years.player_id` → `wc_players.id`

### Requirement: Position normalization

Loaders SHALL map `goal_keeper`/`defender`/`midfielder`/`forward` columns to `positions` array with codes `GK`, `DF`, `MF`, `FW`, and set `primary_position` to the first active code in that order.

#### Scenario: Multi-position player

- **WHEN** a player row has `defender=1` and `midfielder=1`
- **THEN** `positions` contains both `DF` and `MF` and `primary_position` is `DF`

### Requirement: Tournament years expansion

Loaders SHALL split `list_tournaments` on commas into `wc_player_tournament_years` rows.

#### Scenario: Multiple years

- **WHEN** `list_tournaments` is `"1995, 1999"`
- **THEN** two bridge rows exist for years 1995 and 1999

#### Scenario: Count consistency

- **WHEN** loading the full Bronze `players.csv`
- **THEN** for every player, bridge row count equals `count_tournaments`

### Requirement: Players ETL CLI

The system SHALL provide `run.py players` that upserts all players and reloads tournament year bridge rows.

#### Scenario: Full load counts

- **WHEN** `run.py players` runs on project Bronze data
- **THEN** `wc_players` has 10401 rows

### Requirement: Unit tests for player transforms

Transform helpers for positions and year splitting SHALL have unit tests.

#### Scenario: Year split test

- **WHEN** splitting `"1995, 1999"`
- **THEN** result is `[1995, 1999]`
