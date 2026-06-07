## Why

EP04-01 P0/P1 已完成；P2 继续入库剩余比赛事件 CSV，先落地 **换人** 与 **点球大战逐球**。

## What Changes

- `wc_substitutions`（10,222 行）← `substitutions.csv`
- `wc_penalty_kicks`（396 行）← `penalty_kicks.csv`
- Alembic `007`、loader、`run.py subpen`、validate 行数

## Capabilities

### New Capabilities

- `worldcup-silver-sub-pen`: P2 换人 + 点球逐球 Silver 表。
