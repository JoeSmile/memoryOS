## Context

- 规划文档：[`docs/superpowers/specs/2026-06-03-worldcup-bronze-etl-plan.md`](../../../docs/superpowers/specs/2026-06-03-worldcup-bronze-etl-plan.md)
- Bronze 路径：`data/bronze/worldcup/`（31 CSV，本地 gitignore；报告进 Git）
- 运行环境：与 `apps/api` 共用 Conda/venv（`bash scripts/api.sh exec python ...`）

## Goals / Non-Goals

**Goals**

- TEXT 自然键 PK（`T-01`、`WC-2022`）与 CSV 一致
- `wc_tournaments.slug`：`WC-2022` → `wc2022`（EP11 对齐）
- `not applicable` / 空 wiki → NULL
- `0`/`1` → boolean；`upsert` 幂等

**Non-Goals**

- players / matches（后续 change）
- REST API 暴露世界杯数据
- Harness L1（无新路由）

## Schema（摘要）

| 表 | PK | 主要 FK |
|:---|:---|:--------|
| `wc_confederations` | `id` (CF-*) | — |
| `wc_teams` | `id` (T-*) | `confederation_id` |
| `wc_tournaments` | `id` (WC-*) | — |
| `wc_stadiums` | `id` (S-*) | — |

## ETL 运行

```bash
pnpm db:migrate
bash scripts/api.sh exec python ../../scripts/etl/worldcup/run.py dimensions
```

使用现有 `AsyncSessionLocal` + `DATABASE_URL`（asyncpg）。

## Decisions

- 模型注册在 `app.models` 供 Alembic autogenerate/metadata 发现
- Loader 放 `app/etl/worldcup/` 便于 pytest；`scripts/etl/worldcup/run.py` 仅 CLI 入口
- 球队宽表冗余列（`confederation_name`）**不入库**，仅 FK
