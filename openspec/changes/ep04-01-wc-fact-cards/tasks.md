## §0 Human review

- [x] **Tasks reviewed by human** — 用户指定「继续 task」

---

## 1. Generator

- [x] 1.1 `app/etl/worldcup/fact_cards.py`（JOIN 查询 + 文本模板 + JSONL 写入）
  - 预计文件：1 · 层：`etl`

- [x] 1.2 `scripts/etl/worldcup/fact_cards.py` CLI
  - 预计文件：1 · 层：`scripts`

## 2. Tests & output

- [x] 2.1 `tests/unit/test_worldcup_fact_cards.py`（纯函数）
  - 预计文件：1 · 层：`tests`

- [x] 2.2 运行导出 + `samples.jsonl` 10 条；更新 epic / data-model / README
  - 预计文件：≤3 · 层：`docs` / `data`
