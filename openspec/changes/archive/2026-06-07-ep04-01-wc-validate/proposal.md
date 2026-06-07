## Why

Silver 表已分批入库（profile → dimensions → players → matches → events），需要 **可重复运行的集成校验** 与 **技术文档**，作为 EP04 RAG / fact-cards 前的质量门。

## What Changes

- `app/etl/worldcup/validate.py` + `scripts/etl/worldcup/validate.py`
- `docs/tech/worldcup-data-model.md`（ER + 表说明）
- 单元测试（纯逻辑 + 可选 DB 集成）
- `--tournament WC-2022` 黄金集冒烟

## Capabilities

### New Capabilities

- `worldcup-silver-validate`: Silver 引用完整性 + 业务规则校验 CLI。

### Modified Capabilities

- （无）
