## Why

EP04-01 已交付世界杯 **Gold 事实卡**（`matches.jsonl`、`player_careers.jsonl` 等），但 EP04 RAG 管线尚未落地：无 `document_chunks`、无 pgvector、无法语义检索。本 change 建立 **最小可验证 RAG 底座**（摄入 + 向量检索 API），为后续 LangChain/LlamaIndex 双栈与聊天接入铺路。

## What Changes

- Docker PostgreSQL 切换为 **pgvector** 镜像；Alembic `011` 启用 `vector` 扩展并创建 `documents` / `document_chunks` 表。
- **Mock embedding**（无 `OPENAI_API_KEY` 时，Harness 无需外网）+ 可选 OpenAI 兼容真实嵌入（DashScope）。
- World Cup Gold **全量 JSONL 摄入**（`fact_cards/` 下 5 文件；幂等 upsert）；CLI `ingest_worldcup`。
- **`POST /api/v1/knowledge/search`** 向量检索（TopK、collection 过滤、引用元数据）。
- **`POST /api/v1/knowledge/ingest/worldcup`** 开发用摄入端点（Harness 契约）。
- Harness `test_rag_contract.py`；更新 `docs/database.md`。
- 技术笔记 [`docs/tech/rag-embedding-chunking.md`](../../docs/tech/rag-embedding-chunking.md)：切块/embedding 方法、坑、面试要点；实施时填 §6。

**Non-Goals（本 change 不做；Story 4.1–4.2 本史诗暂不排期，无 task）：**

- 前端 `/knowledge` 上传页、PDF/MD 用户上传解析
- LangChain/LlamaIndex 完整生成链与聊天集成（Story 4.4–4.6）
- 双模式切换、LlamaIndex 自研管线（Story 4.5、4.7）

## Capabilities

### New Capabilities

- `rag-schema`: pgvector 扩展与 `documents` / `document_chunks` 表结构
- `rag-ingest`: World Cup JSONL 幂等摄入与 CLI
- `rag-retrieval`: 向量相似度检索 API 与响应契约

### Modified Capabilities

- `postgres-infra`: 本地 Postgres 镜像须预装 pgvector 扩展

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `infra/docker/` | Postgres 镜像 → `pgvector/pgvector:pg16` |
| `apps/api/` | Alembic `011`、models、repositories、services、routes |
| `scripts/etl/rag/` | 新 CLI `ingest_worldcup.py` |
| `tests/harness/` | `test_rag_contract.py` |
| `docs/database.md` | RAG 表文档 |
| 依赖 | `pgvector`（SQLAlchemy）、可选 `langchain-openai` 嵌入（若已有则复用） |
