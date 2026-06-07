## Why

Silver `wc_*` 表与校验已完成；EP04 RAG 需要 **预清洗文本事实卡**（含 `source_ids` 可回溯），不直接查 PG 做 chunk。

## What Changes

- `app/etl/worldcup/fact_cards.py` + `scripts/etl/worldcup/fact_cards.py`
- 输出 `data/gold/worldcup/fact_cards/{matches,players,tournaments}.jsonl`
- 可选 `--tournament WC-2022` 缩小范围；`samples.jsonl` 10 条 spot-check
- 单元测试（纯文本格式化，无 DB）

## Capabilities

### New Capabilities

- `worldcup-gold-fact-cards`: Silver JOIN → JSONL 事实卡导出。

### Modified Capabilities

- （无）
