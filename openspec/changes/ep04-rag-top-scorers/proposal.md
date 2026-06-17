## Why

用户问「2022世界杯射手榜前10名」时，RAG 应直接回答，不应依赖 Tavily。当前向量检索 top 命中为 **比赛卡**（单场进球列表），**Mbappé/Messi 等 `player_career` 卡连 top 50 都进不了**；同时 `compute_rag_sufficient` 仅看分数与年份，误判为「足够」。根因是 Gold 层 **缺少按届聚合的射手榜事实卡**，且榜单类 query 无专门召回/充分性判定。

## What Changes

- Gold ETL：从 Silver `wc_goals` 聚合生成 **`tournament_scorers`** 事实卡（每届一条，含 top N 射手排名文本），输出 `tournament_scorers.jsonl`
- Ingest：将新 JSONL 纳入 `KnowledgeIngestService` 默认 collection 集合并支持 re-ingest
- RAG 充分性：`compute_rag_sufficient` 对 **榜单/排名类** query 要求命中聚合卡或等价排名文本，避免「仅有 match 卡」判 sufficient
- 评测：固定 query「2022世界杯射手榜前10名」的 retrieval harness + 单元测试
- 文档：EP04-01 / EP04 史诗勾选；本地 dev 需先加载 `wc_goals`（`run.py events`）

**Non-Goals：**

- Hybrid/BM25/重排（→ EP04-03）
- Text2SQL 或运行时查 PG 做榜单
- 引入 `top-scorers-summary.csv` bronze 文件（弱键，设计文档已弃用）
- 前端/UI 变更

## Capabilities

### New Capabilities

- `worldcup-gold-top-scorers`: 从 `wc_goals` 聚合生成可检索的届别射手榜 Gold 事实卡

### Modified Capabilities

- `rag-chat`: 榜单/排名类问题的 `rag_sufficient` 判定 — 仅有比赛卡不足以视为 sufficient

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/app/etl/worldcup/fact_cards.py` | 新增聚合卡生成与 export |
| `data/gold/worldcup/fact_cards/` | 新 `tournament_scorers.jsonl`；`samples.jsonl` 增 WC-2022 射手榜样例 |
| `apps/api/app/services/knowledge_ingest_service.py` | 默认 stems +1 |
| `apps/api/app/graphs/prompts/unified_react.py` | 榜单 query 充分性规则 |
| `apps/api/tests/` | unit + harness retrieval case |
| `docs/tasks/epics/EP04-rag.md` · `EP04-01-worldcup-data-etl.md` | Story 勾选 |
| 运维 | 需 re-export Gold + re-ingest；本地 DB 须已跑 `events` ETL |
