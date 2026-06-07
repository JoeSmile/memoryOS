## Context

- `matches.csv`：1,248 行，已含 home/away 比分
- `team_appearances.csv`：2,496 行 = 2× 场次
- 8 场重赛：`replayed=1` 原场 + `replay=1` 重赛，按 `(tournament_id, match_name)` 配对

## Schema

**wc_matches** — PK `id` (`match_id`)

FK：`tournament_id`, `stadium_id`, `home_team_id`, `away_team_id`, `replay_of_match_id` (self)

**wc_team_match_stats** — PK `(match_id, team_id)`

球队视角：`goals_for`, `goals_against`, `is_home`, `won`/`lost`/`drew`

## Validation (load-time)

- 每场 `team_appearances` 恰好 2 行
- `team_appearances` 比分与 `matches` 一致

## CLI

```bash
bash scripts/api.sh exec python ../../scripts/etl/worldcup/run.py matches
```
