# worldcup-silver-matches

Silver 层比赛与球队视角统计。

## ADDED Requirements

### Requirement: Match tables via Alembic

Migration `005_wc_matches` SHALL create `wc_matches` and `wc_team_match_stats`.

#### Scenario: FK graph

- **WHEN** migration applies
- **THEN** `wc_matches` references `wc_tournaments`, `wc_stadiums`, `wc_teams`
- **AND** `wc_team_match_stats` references `wc_matches` and `wc_teams`

### Requirement: Replay linkage

`wc_matches` SHALL store `is_replayed`, `is_replay`, and nullable `replay_of_match_id` for replay rows.

#### Scenario: Italy vs Spain 1934

- **WHEN** `M-1934-13` (`replay=1`) is loaded
- **THEN** `replay_of_match_id` is `M-1934-12`

### Requirement: Team appearances validation

Loader SHALL reject data when team appearance rows do not align with match scores.

#### Scenario: Score consistency

- **WHEN** loading full Bronze data
- **THEN** zero validation errors for team appearance vs match scores

### Requirement: Full load counts

- **WHEN** `run.py matches` completes on project Bronze
- **THEN** `wc_matches` has 1248 rows and `wc_team_match_stats` has 2496 rows
