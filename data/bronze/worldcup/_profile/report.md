# World Cup Bronze — Profile Report

- **Generated**: 2026-06-07T07:00:54.954684+00:00
- **Bronze dir**: `/Users/guowei/Desktop/github/memoryOS/data/bronze/worldcup`
- **Files**: 31

## File inventory

| File | Rows | SHA256 (short) | Columns |
| :--- | ---: | :--- | ---: |
| award_winners.csv | 200 | `84deded971da…` | 12 |
| awards.csv | 8 | `80ff600291b8…` | 5 |
| bookings.csv | 3178 | `e1c010ce790f…` | 26 |
| confederations.csv | 6 | `1560c8d8d25c…` | 5 |
| goals-by-minute-summary.csv | 90 | `0a057fecf5b7…` | 3 |
| goals.csv | 3637 | `4fbe990b7f42…` | 27 |
| group_standings.csv | 626 | `3de1d95f81ff…` | 19 |
| groups.csv | 159 | `9c5b27464ff2…` | 7 |
| host_countries.csv | 31 | `bac4e724d1e8…` | 7 |
| manager_appearances.csv | 2538 | `33f39d48fd60…` | 17 |
| manager_appointments.csv | 637 | `7ba0a3db430d…` | 10 |
| managers.csv | 475 | `94e4db4acc05…` | 7 |
| matches.csv | 1248 | `037f71876475…` | 37 |
| penalty_kicks.csv | 396 | `cbc58511b92b…` | 19 |
| player_appearances.csv | 27432 | `edab41b99556…` | 21 |
| players.csv | 10401 | `97d61d04b522…` | 13 |
| qualified_teams.csv | 625 | `7774c395295e…` | 8 |
| referee_appearances.csv | 1248 | `c3f213a6d8a1…` | 15 |
| referee_appointments.csv | 668 | `9fbb2841b37d…` | 10 |
| referees.csv | 493 | `f98844856371…` | 10 |
| squads.csv | 13843 | `dafd483504fe…` | 12 |
| stadiums.csv | 240 | `88b1bddb12cd…` | 8 |
| substitutions.csv | 10222 | `dd98a991dcea…` | 24 |
| team_appearances.csv | 2496 | `10daa0692911…` | 36 |
| teams.csv | 88 | `a2d5ef96fade…` | 14 |
| top-scorers-summary.csv | 15 | `be757eda1f7e…` | 3 |
| tournament-appearances.csv | 20 | `ef0773cc4ca1…` | 2 |
| tournament-goals-summary.csv | 22 | `e3053e730df6…` | 3 |
| tournament_stages.csv | 155 | `e4a6606907cf…` | 16 |
| tournament_standings.csv | 120 | `a1649d448bb7…` | 7 |
| tournaments.csv | 30 | `906b122d80aa…` | 18 |

## Semantic alias groups

### tournament
- 赛会标识；多文件重复贴标
- Columns: `tournament_id`, `tournament_name`

### team_identifiers
- 球队 ID；视角不同（主客/对手/球员所属队）
- Columns: `team_id`, `home_team_id`, `away_team_id`, `opponent_id`, `player_team_id`

### team_labels
- 球队名称冗余列
- Columns: `team_name`, `home_team_name`, `away_team_name`, `opponent_name`, `player_team_name`

### match_ref
- 比赛引用
- Columns: `match_id`, `match_name`, `match_date`

### score_team_perspective
- 球队相对视角进球
- Columns: `goals_for`, `goals_against`, `goal_differential`

### score_match_perspective
- 比赛主客绝对比分
- Columns: `home_team_score`, `away_team_score`, `home_team_score_margin`, `away_team_score_margin`

### win_flags
- 胜负标志；matches 主客 vs team_appearances 当前队
- Columns: `home_team_win`, `away_team_win`, `win`, `lose`, `draw`

### penalty_shootout
- 点球大战比分
- Columns: `penalties_for`, `penalties_against`, `home_team_score_penalties`, `away_team_score_penalties`

## FK spot checks

| Child | Parent | Orphans |
| :--- | :--- | ---: |
| goals.csv.match_id | matches.csv.match_id | 0 |
| goals.csv.player_id | players.csv.player_id | 0 |
| squads.csv.player_id | players.csv.player_id | 0 |
| squads.csv.team_id | teams.csv.team_id | 0 |
| matches.csv.home_team_id | teams.csv.team_id | 0 |
| team_appearances.csv.match_id | matches.csv.match_id | 0 |

## High-frequency shared columns

| Column | # Files |
| :--- | ---: |
| `country_name` | 9 |
| `family_name` | 14 |
| `given_name` | 14 |
| `group_name` | 11 |
| `key_id` | 27 |
| `match_date` | 9 |
| `match_id` | 9 |
| `match_name` | 9 |
| `player_id` | 8 |
| `stage_name` | 12 |
| `team_code` | 15 |
| `team_id` | 15 |
| `team_name` | 17 |
| `tournament_id` | 20 |
| `tournament_name` | 21 |
