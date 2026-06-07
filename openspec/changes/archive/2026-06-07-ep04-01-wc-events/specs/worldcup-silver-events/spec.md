# worldcup-silver-events

Silver 层比赛事件：进球、名单、红黄牌。

## ADDED Requirements

### Requirement: Event tables via Alembic

Migration `006_wc_events` SHALL create `wc_goals`, `wc_squads`, and `wc_bookings` with FKs to existing dimension/match/player tables.

### Requirement: Goals preserve own-goal semantics

`wc_goals` SHALL store both `team_id` (credited) and `player_team_id` (scorer's club).

### Requirement: Squads composite key

`wc_squads` primary key SHALL be `(tournament_id, team_id, player_id)`.

### Requirement: Events CLI load counts

`run.py events` on full Bronze SHALL load 3637 goals, 13843 squads, 3178 bookings.
