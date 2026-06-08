## Context

- **现状**：`data/gold/worldcup/fact_cards/*.jsonl` 每行已是 `{id, entity_type, source_ids, text}` 预格式化事实卡；EP04-01 明确 **不写 pgvector**。
- **约束**：Harness 无外网；嵌入与 chat 共用 `OPENAI_API_KEY` / DashScope 兼容 base；分层 `api → services → repositories`；改路由必 Harness。
- **Gold 全量**（`data/gold/worldcup/fact_cards/`）：`matches` 1248 · `players` 10401 · `player_careers` 10401 · `tournaments` 30 · `samples` 10。

## Goals / Non-Goals

**Goals:**

- 本地 `pnpm db:up` + `pnpm db:migrate` 后具备 pgvector 与 RAG 表。
- 一键摄入 **全部 5 个 Gold JSONL**；重复摄入不重复插 chunk。
- `POST /knowledge/search` 返回 TopK 片段 + `document_id` / `external_id` / `entity_type` / `score`。
- Mock 嵌入维度固定（如 **384**），与 migration `vector(384)` 一致。

**Non-Goals:**

- 上传 UI、PDF 解析、语义切块、重排、Query 改写、RAG 生成答案。
- 生产级 embedding 批处理队列；本 change 同步摄入即可（Gold 数据量可接受）。

### D8: 切块 / Embedding 技术文档

- 方法论、踩坑、面试要点写入 [`docs/tech/rag-embedding-chunking.md`](../../../docs/tech/rag-embedding-chunking.md)。
- **task 2.3 / 3.4**：实现前后与人讨论，**必填**文档 §6 实施记录；archive 前不得留空。

## Decisions

### D1: Postgres 镜像

- **选** `pgvector/pgvector:pg16` 替换 `postgres:16-alpine`。
- **替代**：手动 `CREATE EXTENSION` on alpine — 运维成本高，弃用。

### D2: 表模型

```text
documents
  id UUID PK
  collection VARCHAR(64) NOT NULL     -- e.g. worldcup-matches, worldcup-player-careers
  external_id VARCHAR(128) NOT NULL -- JSONL id field
  entity_type VARCHAR(64)
  source_ids JSONB
  metadata JSONB                      -- optional extras
  created_at / updated_at
  UNIQUE (collection, external_id)

document_chunks
  id UUID PK
  document_id FK → documents CASCADE
  chunk_index INT NOT NULL DEFAULT 0  -- fact card V1: always 0
  content TEXT NOT NULL
  embedding vector(384) NOT NULL
  token_count INT                     -- optional estimate
  created_at
  UNIQUE (document_id, chunk_index)
```

- 无独立 `knowledge_collections` 表；`collection` 字符串足够 V1。

### D3: 一块一卡（无二次切块）

- Gold JSONL 的 `text` 字段直接写入 `document_chunks.content`（`chunk_index=0`）。
- 后续 PDF/MD change 再引入 splitter。

### D4: Embedding

| 模式 | 条件 | 行为 |
|:-----|:-----|:-----|
| Mock | `OPENAI_API_KEY` 未设置 | 确定性伪向量（hash → 384 floats，L2 归一化） |
| Live | Key 已设置 | `text-embedding-3-small` 或 DashScope 兼容 `embeddings` API |

- Settings：`embedding_model`、`embedding_dimensions=384`（mock 与 live 维度须一致；live 若模型为 1536 则 V2 change 再调 migration——**V1 统一 mock 384，live 也用 small 并 truncate/project 或选 384 维模型**）。
- **V1 简化**：mock 384；live 使用 `text-embedding-3-small` with `dimensions=384`（OpenAI API 支持降维）。

### D5: 摄入幂等

- Upsert `documents` on `(collection, external_id)`。
- Replace chunk：delete old chunks for document → insert new（或 upsert chunk_index=0）。
- Collection 命名：`worldcup-{stem}`，stem = 文件名去 `.jsonl`（如 `worldcup-matches`）。
- CLI 默认全量 5 文件；可选 `--collections matches,player_careers` subset。
- `samples.jsonl` 与主文件有内容重叠，但 collection 不同，仍默认摄入（便于 demo 小集检索）。

### D6: 检索 API

```http
POST /api/v1/knowledge/search
Authorization: Bearer <token>
{ "query": "Messi World Cup goals", "collection": "worldcup-player-careers", "top_k": 5 }
```

- SQL：`ORDER BY embedding <=> query_vector LIMIT top_k`（cosine distance）。
- 响应 `data.chunks[]`: `{ content, score, document_id, external_id, entity_type, collection }`。

### D7: 摄入 API（Harness / dev）

```http
POST /api/v1/knowledge/ingest/worldcup
Authorization: Bearer <token>
{ "collections": null }
```

- `collections` 省略或 `null` → 摄入全部 5 个 Gold JSONL；数组 → 仅指定 stem。
- 从仓库固定路径 `data/gold/worldcup/fact_cards/{name}.jsonl` 读取。
- 生产可后续改为仅 CLI、禁 HTTP。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| 换 Postgres 镜像需重建 volume | README 注明一次性 `docker compose down -v` |
| 10401 条同步嵌入慢（live） | Harness 用 mock；本地 dev 可分批 |
| 384 维与后续模型不一致 | `embedding_model` + migration 版本化，换模型需 re-embed change |
| ingest HTTP 暴露 | V1 需 JWT；后续加 admin role |

## Migration Plan

1. `docker compose down -v` → 更新镜像 → `docker compose up -d`（人审确认可清空本地数据）
2. `pnpm db:migrate` → `011`
3. `ingest_worldcup` CLI 或 API
4. Harness 绿

## Open Questions

- [ ] V2 是否将检索接入 LangGraph chat tool？（本 change 不接入）
- [x] Gold 全量 5 jsonl 默认摄入 — **人审确认**
- [x] **A** 本地 dev 用真实 embedding API；CI/Harness mock — **人审确认**
- [x] **B** V1 全量 5 jsonl 摄入（含 `players` + `player_careers`）；search 默认不限 collection — **人审确认**
- [x] **C** 本 change 不接入聊天 — **人审确认**
- [ ] Ollama 本地 embedding/LLM 是否作为 V2 可选后端？（见 `rag-embedding-chunking.md` §3.8）
