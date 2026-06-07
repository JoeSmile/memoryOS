## §0 Human review

- [x] **Tasks reviewed by human** — 用户说「继续 dim-teams」

---

## 1. Schema

- [x] 1.1 ORM models `wc_confederations` / `wc_teams` / `wc_tournaments` / `wc_stadiums` + register in `app.models`
  - 预计文件：2 · 层：models

- [x] 1.2 Alembic `003_wc_dimension_tables`
  - 预计文件：1 · 层：alembic

## 2. ETL

- [x] 2.1 `app/etl/worldcup/transforms.py` + `loaders/dimensions.py`（upsert 顺序加载）
  - 预计文件：2 · 层：etl

- [x] 2.2 `scripts/etl/worldcup/run.py` CLI `dimensions` 子命令
  - 预计文件：1 · 层：scripts

## 3. Tests & verify

- [x] 3.1 `tests/unit/test_worldcup_dimensions.py`（transforms + 可选 integration skip）
  - 预计文件：1 · 层：unit

- [x] 3.2 `pnpm db:migrate` + dimension load 行数验收（6/88/30/240）
  - 预计文件：0 · 命令验证
