## Why

Bronze profile（`ep04-01-wc-profile`）已完成，但 Silver 层尚无表结构与入库路径。维度表（足联、球队、赛会、场馆）是后续 `matches` / `players` ETL 的外键根，必须先落地。

## What Changes

- Alembic `003_wc_dimension_tables`：`wc_confederations`、`wc_teams`、`wc_tournaments`、`wc_stadiums`
- ORM models（`app/models/worldcup/`）
- ETL：`app/etl/worldcup/` transforms + dimension loaders（upsert、wiki 清洗、`slug` 映射）
- CLI：`scripts/etl/worldcup/run.py dimensions`
- 单元测试：transform 函数 + loader 行数断言（mock/async）

## Capabilities

### New Capabilities

- `worldcup-silver-dimensions`: 世界杯维度表 schema 与 Bronze→Silver 加载。

### Modified Capabilities

- （无）

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/alembic/versions/` | 新 migration 003 |
| `apps/api/app/models/` | worldcup 模型 |
| `apps/api/app/etl/worldcup/` | loaders（新目录） |
| `scripts/etl/worldcup/run.py` | CLI |
| PostgreSQL | 新增 4 张 `wc_*` 表 |
