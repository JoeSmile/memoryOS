## §0 Human review（apply 前必过）

- [x] **Tasks reviewed by human** — 用户确认「开始 ep04-01-wc-profile」

### Review checklist

- [x] 仅 Story 01.1 scope，无 Silver/Alembic
- [x] 不动 `apps/api` 业务路由
- [x] 每条 task ≤3 文件

**Reviewer notes:** 用户 2026-06-07 明确要求开始本 change。

---

## 1. 依赖与脚本骨架

- [x] 1.1 `requirements-dev.txt` 增加 `pandas`；新建 `scripts/etl/worldcup/profile.py` 入口与 CLI
  - 预计文件：2 · 层：scripts + dev deps

## 2. Profile 核心逻辑

- [x] 2.1 实现 per-file hash/行数/列统计 + `column_index` + `semantic_groups` + `fk_checks`
  - 预计文件：1 · 层：`scripts/etl/worldcup/profile.py`

## 3. 输出与文档

- [x] 3.1 生成 `data/bronze/worldcup/_profile/manifest.json` 与 `report.md`；更新 Bronze README
  - 预计文件：3 · 层：data + docs

## 4. 测试与验收

- [x] 4.1 新增 `fixtures/` 与 `tests/unit/test_worldcup_profile.py`；本地跑 profile + pytest 绿灯
  - 预计文件：3 · 层：tests + fixtures
