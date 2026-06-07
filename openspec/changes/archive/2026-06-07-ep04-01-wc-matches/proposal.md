## Why

球员与维度表已入库；`goals` / `squads` / `player_appearances` 均依赖 `match_id`。需将 `matches.csv`（canonical）与 `team_appearances.csv`（球队视角）写入 Silver。

## What Changes

- Alembic `005_wc_matches`：`wc_matches`、`wc_team_match_stats`
- 重赛字段：`is_replayed`、`is_replay`、`replay_of_match_id`（8 场）
- Loader + 加载时比分交叉校验
- `run.py matches`

## Capabilities

### New Capabilities

- `worldcup-silver-matches`: 比赛主表与球队视角统计 ETL。

### Modified Capabilities

- （无）

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/alembic/versions/005_*` | 新迁移 |
| `apps/api/app/models/worldcup/matches.py` | 模型 |
| `apps/api/app/etl/worldcup/loaders/matches.py` | loader |
