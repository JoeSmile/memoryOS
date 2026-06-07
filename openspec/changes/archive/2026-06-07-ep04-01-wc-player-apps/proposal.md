## Why

P2 最大表 `player_appearances.csv`（27,432 行）记录每场每球员出场（首发/替补、位置），补全 Silver 比赛参与数据。

## What Changes

- `wc_player_appearances` PK `(match_id, team_id, player_id)`
- Alembic `008`、`loaders/player_appearances.py`、`run.py appearances`
