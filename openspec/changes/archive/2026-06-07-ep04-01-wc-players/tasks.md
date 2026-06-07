## §0 Human review

- [x] **Tasks reviewed by human** — 用户说「继续 players」

---

## 1. Schema

- [x] 1.1 Models `wc_players` + `wc_player_tournament_years`；Alembic `004`
  - 预计文件：3 · 层：models + alembic

## 2. ETL

- [x] 2.1 `transforms` 扩展 + `loaders/players.py` + `run.py players`
  - 预计文件：3 · 层：etl + scripts

## 3. Tests & verify

- [x] 3.1 `test_worldcup_players.py`；migrate + load 10401 行
  - 预计文件：1 · 层：unit
