## 0. Human review（apply 前必过）

> propose 完成后 **必须停在这里**等人审；未勾选前 **禁止** 写业务代码。

- [x] **Tasks reviewed by human** — 人审通过后再 `/opsx:apply`、`/work-next` 或说「继续实现」

### Review checklist

- [ ] 本 change **不含** 前端上传/PDF 解析（Story 4.1–4.2 本史诗暂不排期，无对应 task）
- [ ] Harness 覆盖 design scenarios（ingest 幂等、search、401、mock embed）
- [ ] 与 EP04 Story 4.3–4.4 首 slice 一致；无 LlamaIndex/聊天生成 scope 膨胀
- [ ] 每条 task ≤3 文件 / ~150 行

**Reviewer notes:**

- **人审确认（2026-06-03）**：砍掉前端上传相关 task；Gold 目录 **全部 5 个 jsonl** 默认摄入；本地 DB 可 `docker compose down -v` 全量重建。
- **A Embedding**：本地开发对接 **真实 API**（DashScope OpenAI 兼容）；Harness/CI 仍用 mock（无外网）。
- **B 摄入**：V1 **全量** 5 个 jsonl（`players` + `player_careers` 均保留，便于定位召回问题）。
- **C 范围**：本 change **不接入聊天**；仅 ingest + `POST /knowledge/search`。
- **文档**：[`rag-embedding-chunking.md`](../../../docs/tech/rag-embedding-chunking.md) — task 2.3/3.4 填 §6。
- **依赖：** EP04-01 ✅ · EP03 ✅

---

## 1. Infrastructure

- [x] 1.1 Docker Postgres → `pgvector/pgvector:pg16` + `infra/docker/README.md`
  - 预计文件：2 · 层：infra

- [x] 1.2 Alembic `011`：`vector` 扩展 + `documents` / `document_chunks` + SQLAlchemy models
  - 预计文件：3 · 层：alembic、models

- [x] 1.3 更新 `docs/database.md` RAG 表说明
  - 预计文件：1 · 层：docs

## 2. Embedding

- [x] 2.1 `Settings` 嵌入配置 + `EmbeddingService`（mock 1024 维 + 百炼 v4 live）
  - 预计文件：2 · 层：core、services

- [x] 2.2 unit：`tests/unit/test_embedding_service.py` mock 确定性
  - 预计文件：1 · 层：tests

- [x] 2.3 **与人讨论** embedding 决策（mock/live、batch、重试）并更新 `docs/tech/rag-embedding-chunking.md` §3 + §6
  - 预计文件：1 · 层：docs（**archive 前 §6 不得留空**）

## 3. Ingest

- [x] 3.1 `DocumentRepository` + `DocumentChunkRepository`
  - 预计文件：2 · 层：repositories

- [x] 3.2 `KnowledgeIngestService`：摄入 `fact_cards/` 下全部 Gold JSONL（5 文件，见 design D5）
  - 预计文件：2 · 层：services
  - 默认：`matches`、`players`、`player_careers`、`tournaments`、`samples`

- [x] 3.3 CLI `scripts/etl/rag/ingest_worldcup.py`（默认全量；`--collections` 可 subset）
  - 预计文件：1 · 层：scripts

- [ ] 3.4 **与人讨论** 切块/摄入策略（路径 A 一卡一块、双 collection 球员）并更新 `rag-embedding-chunking.md` §2 + §6
  - 预计文件：1 · 层：docs

## 4. Retrieval API

- [x] 4.1 Harness `tests/harness/test_rag_contract.py`（ingest + search + 401）
  - 预计文件：1 · 层：tests（TDD 先写）

- [x] 4.2 `KnowledgeSearchService` + schemas
  - 预计文件：2 · 层：services、schemas

- [ ] 4.3 Router `POST /knowledge/search` + `POST /knowledge/ingest/worldcup` + 注册 main
  - 预计文件：2 · 层：api

## 5. Closeout

- [ ] 5.1 `pnpm db:migrate` + `pnpm test:api:harness` 全绿；勾选 EP04-rag Story 4.3/4.4 首项
  - 预计文件：1 · 层：docs/epic

- [ ] 5.2 archive change
  - 预计文件：0 · openspec archive
