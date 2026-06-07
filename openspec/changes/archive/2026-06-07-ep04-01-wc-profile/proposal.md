## Why

EP04-01 世界杯 ETL 的 31 个 Bronze CSV 已就位，但 Silver 建表与 loader 不能凭假设动手。需要 **可复现的资产盘点**（行数、主键、列共现、外键抽检、文件 hash），作为后续 `wc_*` 迁移与 ETL change 的输入。

本 change **仅覆盖 Story 01.1**（Bronze profile）；不写 PostgreSQL 表、不做入库。

## What Changes

- 新增 `scripts/etl/worldcup/profile.py`：扫描 `data/bronze/worldcup/*.csv`，输出 JSON manifest + Markdown 报告。
- 输出目录 `data/bronze/worldcup/_profile/`（`manifest.json`、`report.md`），可进 Git（CSV 仍 gitignore）。
- `apps/api/requirements-dev.txt` 增加 `pandas`（仅 ETL/测试开发依赖）。
- 单元测试：对 fixture 小样目录跑 profile，断言 manifest 结构。
- 更新 `data/bronze/worldcup/README.md` 运行说明。

## Capabilities

### New Capabilities

- `worldcup-bronze-profile`: Bronze CSV 盘点脚本、manifest、报告与列名/外键抽检约定。

### Modified Capabilities

- （无）

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `scripts/etl/worldcup/` | 新建 profile 脚本 |
| `data/bronze/worldcup/_profile/` | 生成物（进 Git） |
| `apps/api/requirements-dev.txt` | +pandas |
| `apps/api/tests/unit/` | profile 单测 |
| EP04-01 后续 change | 依赖 manifest 定表映射 |
