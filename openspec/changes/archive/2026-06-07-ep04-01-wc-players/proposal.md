## Why

维度表（`ep04-01-wc-dim-teams`）已入库；`matches` / `squads` / `goals` 均依赖 `player_id` FK。需将 `players.csv` 规范化入 `wc_players`，并把 `list_tournaments` 展开为 `wc_player_tournament_years` 桥表。

## What Changes

- Alembic `004_wc_players`：`wc_players`、`wc_player_tournament_years`
- ORM models + `loaders/players.py`
- `transforms` 扩展：位置列 → `positions[]`、`primary_position`；年份列表解析
- `run.py players` 子命令
- 单元测试 + 入库验收（10,401 球员）

## Capabilities

### New Capabilities

- `worldcup-silver-players`: 球员维度与参赛年份桥表 ETL。

### Modified Capabilities

- （无）

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/alembic/versions/004_*` | 新迁移 |
| `apps/api/app/models/worldcup/` | players 模型 |
| `apps/api/app/etl/worldcup/` | players loader |
| `scripts/etl/worldcup/run.py` | `players` CLI |
