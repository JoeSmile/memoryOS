# worldcup-bronze-profile

Bronze 层世界杯 CSV 资产盘点与 profiling 报告。

## ADDED Requirements

### Requirement: Profile script scans Bronze CSV directory

The system SHALL provide `scripts/etl/worldcup/profile.py` that accepts a Bronze directory path containing `*.csv` files and writes profiling output to `<bronze_dir>/_profile/`.

#### Scenario: Successful profile run

- **WHEN** the operator runs `python scripts/etl/worldcup/profile.py data/bronze/worldcup/`
- **THEN** `_profile/manifest.json` and `_profile/report.md` are created or updated
- **AND** `manifest.json` lists every `*.csv` in the directory with `sha256`, `row_count`, and `columns`

#### Scenario: Missing directory

- **WHEN** the path does not exist or contains no CSV files
- **THEN** the script exits with non-zero status and prints an error message

### Requirement: Manifest includes cross-file column index

The manifest SHALL include a `column_index` mapping each column name to the list of CSV files that contain it.

#### Scenario: Shared column detection

- **WHEN** `tournament_id` appears in multiple CSV files
- **THEN** `column_index.tournament_id` lists all those file names

### Requirement: Manifest includes semantic alias groups

The manifest SHALL include `semantic_groups` documenting known same-meaning column name clusters (e.g. `team_id` vs `home_team_id`).

#### Scenario: Team identifier cluster

- **WHEN** profiling completes on the full Bronze dataset
- **THEN** a semantic group for team identifiers references `team_id`, `home_team_id`, `away_team_id`, `opponent_id`, and `player_team_id` where present

### Requirement: Foreign-key spot checks

The profiler SHALL run configured FK spot checks between CSV pairs and record `orphan_count` in `fk_checks`.

#### Scenario: Goals reference matches

- **WHEN** both `goals.csv` and `matches.csv` are present
- **THEN** `fk_checks` includes an entry for `goals.match_id` → `matches.match_id` with `orphan_count` equal to the number of goal rows whose `match_id` is not in `matches`

#### Scenario: Zero orphans on bundled dataset

- **WHEN** profiling runs on the project's full Bronze World Cup CSV set
- **THEN** `goals.match_id` → `matches.match_id` has `orphan_count` of 0

### Requirement: Profile output is versionable

The `_profile/` directory SHALL be committable to Git while raw `*.csv` in the same Bronze directory remain gitignored.

#### Scenario: Report without CSV in repo

- **WHEN** a clone has no local CSV files but has committed `_profile/manifest.json`
- **THEN** reviewers can read the last profile snapshot without running ETL

### Requirement: Unit test with fixtures

The system SHALL include a unit test that runs the profiler against a minimal fixture directory and asserts manifest structure without requiring full Bronze CSVs.

#### Scenario: CI profile test

- **WHEN** `pytest tests/unit/test_worldcup_profile.py` runs
- **THEN** all tests pass using only fixture CSV files under `scripts/etl/worldcup/fixtures/`
