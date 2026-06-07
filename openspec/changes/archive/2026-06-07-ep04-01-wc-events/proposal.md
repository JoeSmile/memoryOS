## Why

P0（维度/球员/比赛）已入库；`goals`、`squads`、`bookings` 是 RAG 事实卡与赛会分析的高价值事件表，需进入 Silver。

## What Changes

- Alembic `006_wc_events`：`wc_goals`、`wc_squads`、`wc_bookings`
- `loaders/events.py` + `run.py events`
- 单元测试 + 入库验收（3637 / 13843 / 3178）

## Capabilities

### New Capabilities

- `worldcup-silver-events`: 进球、名单、红黄牌 ETL。

### Modified Capabilities

- （无）
