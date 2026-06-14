# MemoryOS 数据库设计

> **真相源**：Alembic 迁移与 ORM 模型。  
> 实现后若迁移有差异，以 `apps/api/alembic/versions/` 为准。

**引擎**：PostgreSQL 16 · **扩展**：`vector`（pgvector，迁移 `011`）

---

##

```mermaid
erDiagram
    users ||--o{ conversations : owns
    users ||--o{ memories : owns
    conversations ||--o{ messages : contains
    documents ||--o{ document_chunks : contains

    users {
        uuid id PK
        string email UK
        string password_hash "nullable until JWT"
        timestamptz created_at
        timestamptz updated_at
    }

    conversations {
        uuid id PK
        uuid user_id FK
        string title
        text context_summary "nullable, EP06 rolling summary"
        timestamptz summary_updated_at "nullable"
        timestamptz created_at
        timestamptz updated_at
    }

    memories {
        uuid id PK
        uuid user_id FK
        string memory_key "upsert key per user"
        string memory_type "preference | fact | constraint"
        text content
        numeric importance "0-1"
        vector embedding "1024-dim, nullable until embed"
        timestamptz expires_at "nullable"
        timestamptz created_at
        timestamptz updated_at
    }

    messages {
        uuid id PK
        uuid conversation_id FK
        string role "user | assistant | system"
        text content
        timestamptz created_at
    }

    documents {
        uuid id PK
        string collection
        string external_id
        string entity_type "nullable"
        jsonb source_ids "nullable"
        jsonb metadata "nullable"
        timestamptz created_at
        timestamptz updated_at
    }

    document_chunks {
        uuid id PK
        uuid document_id FK
        int chunk_index
        text content
        vector embedding "1024-dim"
        int token_count "nullable"
        timestamptz created_at
    }
```

**删除策略**：

- `users` 删除 → 级联删除其 `conversations` → 级联删除其 `messages`；级联删除其 `memories`。
- `documents` 删除 → 级联删除其 `document_chunks`。

---

## 表：`users`

| 列              | 类型           | 约束                            | 说明                        |
| :-------------- | :------------- | :------------------------------ | :-------------------------- |
| `id`            | `UUID`         | PK, default `gen_random_uuid()` | 用户 ID                     |
| `email`         | `VARCHAR(255)` | UNIQUE, NOT NULL                | 登录标识（EP03.4 JWT）      |
| `password_hash` | `VARCHAR(255)` | NULL                            | bcrypt 哈希；`auth/register` 必填，旧 harness 用户可空 |
| `created_at`    | `TIMESTAMPTZ`  | NOT NULL, default `now()`       | UTC                         |
| `updated_at`    | `TIMESTAMPTZ`  | NOT NULL, default `now()`       | UTC                         |

**索引**：`email`（唯一约束隐含）。

---

## 表：`conversations`

| 列           | 类型           | 约束                                        | 说明         |
| :----------- | :------------- | :------------------------------------------ | :----------- |
| `id`         | `UUID`         | PK                                          | 会话 ID      |
| `user_id`    | `UUID`         | FK → `users.id` ON DELETE CASCADE, NOT NULL | 所属用户     |
| `title`               | `VARCHAR(500)` | NOT NULL, default `''`                      | 列表展示标题 |
| `context_summary`     | `TEXT`         | NULL                                        | 会话 rolling 摘要（EP06 · 迁移 `014`） |
| `summary_updated_at`  | `TIMESTAMPTZ`  | NULL                                        | 上次摘要写入时间（节流 rolling 更新） |
| `created_at`          | `TIMESTAMPTZ`  | NOT NULL, default `now()`                   |              |
| `updated_at`          | `TIMESTAMPTZ`  | NOT NULL, default `now()`                   | 最后活动时间 |

**索引（Story 3.5）**：`ix_conversations_user_updated (user_id, updated_at DESC)` — 会话列表（迁移 `010`）。

---

## 表：`messages`

| 列                | 类型          | 约束                                                | 说明                                                       |
| :---------------- | :------------ | :-------------------------------------------------- | :--------------------------------------------------------- |
| `id`              | `UUID`        | PK                                                  | 消息 ID                                                    |
| `conversation_id` | `UUID`        | FK → `conversations.id` ON DELETE CASCADE, NOT NULL |                                                            |
| `role`            | `VARCHAR(32)` | NOT NULL                                            | `user` / `assistant` / `system`（EP02 流式写入 assistant） |
| `content`         | `TEXT`        | NOT NULL                                            | 正文                                                       |
| `created_at`      | `TIMESTAMPTZ` | NOT NULL, default `now()`                           | 排序依据                                                   |

**索引（Story 3.5）**：`ix_messages_conv_created (conversation_id, created_at)` — 拉取历史（迁移 `010`）。

---

## 长期记忆（EP06 · 迁移 `014`）

用户域长期记忆；向量检索与 RAG `document_chunks` 分离（不写入知识库 collection）。

| 项 | 值 |
| :--- | :--- |
| 向量维度 | **1024**（与 RAG 一致 · `app/core/rag_constants.py`） |
| 幂等键 | `(user_id, memory_key)` — 抽取 upsert |
| V1 ANN 索引 | **无**（按用户过滤后暴力 scan + `LIMIT`） |

ORM（task 3.2）：`app/models/memory.py` · Repository：`memory_repository`。

### 表：`memories`

| 列 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | PK, default `gen_random_uuid()` | 记忆 ID |
| `user_id` | `UUID` | FK → `users.id` ON DELETE CASCADE, NOT NULL | 所属用户 |
| `memory_key` | `VARCHAR(128)` | NOT NULL | 规范化 key（同用户 upsert） |
| `memory_type` | `VARCHAR(32)` | NOT NULL | `preference` / `fact` / `constraint` |
| `content` | `TEXT` | NOT NULL | 记忆正文 |
| `importance` | `NUMERIC(4,3)` | NOT NULL, default `0.500` | 0–1 重要性 |
| `embedding` | `vector(1024)` | NULL | 语义向量；抽取后 embed，可为空 |
| `expires_at` | `TIMESTAMPTZ` | NULL | 可选过期时间 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | 覆盖 upsert 时更新 |

**约束**：

- `uq_memories_user_memory_key (user_id, memory_key)`
- `ck_memories_memory_type` — 类型枚举
- `ck_memories_importance_range` — `importance` ∈ [0, 1]

**索引**：`ix_memories_user_id (user_id)` — 列表与按用户检索。

---

## RAG（EP04 · 迁移 `011`）

逻辑文档与向量块分表存储；Gold 事实卡一行对应一条 `document` + 一条 `document_chunks`（预格式化，无需二次切块）。详见 [rag-embedding-chunking.md](./tech/rag-embedding-chunking.md)。

| 项 | 值 |
| :--- | :--- |
| 扩展 | `CREATE EXTENSION vector`（Compose 镜像 `pgvector/pgvector:pg16`） |
| 向量维度 | **1024**（`app/core/rag_constants.py` · 百炼 `text-embedding-v4` 默认） |
| 幂等键 | `(collection, external_id)` |
| V1 ANN 索引 | **无**（~2.2 万行暴力 scan + `LIMIT`） |

ORM：`app/models/knowledge.py` · Repository：`document_repository` / `document_chunk_repository`。

---

## 表：`documents`

| 列 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | PK, default `gen_random_uuid()` | 逻辑文档 ID |
| `collection` | `VARCHAR(64)` | NOT NULL | 命名空间，如 `worldcup-fact-cards` |
| `external_id` | `VARCHAR(128)` | NOT NULL | 源侧稳定 ID（如 Gold 行 `id`） |
| `entity_type` | `VARCHAR(64)` | NULL | 实体类型，便于过滤（如 `match`、`player`） |
| `source_ids` | `JSONB` | NULL | 溯源 ID 列表（赛会、球队等） |
| `metadata` | `JSONB` | NULL | 扩展元数据（非检索正文） |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | re-ingest 时更新 |

**约束**：`uq_documents_collection_external_id (collection, external_id)` — 同 collection 下 external_id 唯一。

**索引**：`ix_documents_collection (collection)` — 按 collection 过滤检索。

---

## 表：`document_chunks`

| 列 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | PK, default `gen_random_uuid()` | 块 ID |
| `document_id` | `UUID` | FK → `documents.id` ON DELETE CASCADE, NOT NULL | 所属文档 |
| `chunk_index` | `INTEGER` | NOT NULL, default `0` | 同文档内序号（Gold 事实卡 V1 恒为 `0`） |
| `content` | `TEXT` | NOT NULL | 检索与展示正文 |
| `embedding` | `vector(1024)` | NOT NULL | pgvector 语义向量 |
| `token_count` | `INTEGER` | NULL | 可选 token 统计 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |

**约束**：`uq_document_chunks_doc_index (document_id, chunk_index)` — 同文档 chunk 序号唯一。

**索引**：`ix_document_chunks_document_id (document_id)` — 按文档加载/替换块。

**检索**：V1 使用 `<=>`（余弦距离）或 `<->`（L2）+ `ORDER BY … LIMIT k`；可选 `WHERE collection = …`（join `documents`）。

---

## 枚举说明

`messages.role` 使用 `VARCHAR` 存储，与 OpenSpec
design 一致；后续可改为 PostgreSQL `ENUM` 类型。

| 值          | 含义                            |
| :---------- | :------------------------------ |
| `user`      | 用户输入                        |
| `assistant` | 模型回复（含 SSE 流式拼接结果） |
| `system`    | 系统提示 / 工具指令             |

---

## 本地环境

| 项           | 值                                                               |
| :----------- | :--------------------------------------------------------------- |
| Compose 文件 | `infra/docker/docker-compose.yml`                                |
| 连接串       | `postgresql+asyncpg://memoryos:memoryos@localhost:5432/memoryos` |
| 连接池       | `DB_POOL_SIZE=5`、`DB_MAX_OVERFLOW=10`（见 `apps/api/.env.example`） |
| 启动         | `pnpm db:up`（Postgres + Redis）                                 |
| Redis        | `redis://localhost:6379/0`                                       |

详见 [infra/docker/README.md](../infra/docker/README.md)。

---

## 鉴权（Story 3.4）

- 注册：`POST /api/v1/auth/register` → 写入 `password_hash`（bcrypt）。
- 登录：`POST /api/v1/auth/login` → JWT access token（HS256，`JWT_SECRET`）。
- 当前用户：`GET /api/v1/me`，Header `Authorization: Bearer <token>`。
- Redis key `memoryos:jwt:blacklist:{jti}` 已预留；本 Story 未实现 refresh/黑名单。

详见 [BE-engineering.md](./tech/BE-engineering.md) §4.1。

---

## Redis 缓存（Story 3.3）

PostgreSQL 为真相源；Redis 用于 Cache-Aside 与流式临时数据。

| Key 模式                                        | TTL        | 说明                                    |
| :---------------------------------------------- | :--------- | :-------------------------------------- |
| `memoryos:conversations:user:{user_id}`         | 300s       | 用户会话列表 JSON（`ConversationRead`） |
| `memoryos:stream:{conversation_id}:{stream_id}` | 3600s      | EP02 SSE partial content                |
| `memoryos:jwt:blacklist:{jti}`                  | token 寿命 | Story 3.4 预留                          |

实现：`apps/api/app/cache/` · 配置 `REDIS_URL`。

---

## 后续史诗

| 史诗   | 表/能力                          |
| :----- | :------------------------------- |
| EP03.3 | ✅ Redis 会话列表 + 流式临时缓存 |
| EP03.4 | ✅ JWT、`auth/register` 写入 `password_hash` |
| EP04   | ✅ `documents` / `document_chunks`、pgvector（`011`）；ingest / search API 进行中 |
| EP06   | 记忆相关表扩展                   |

---

## 变更记录

| 日期    | Change              | 说明        |
| :------ | :------------------ | :---------- |
| 2026-06 | `ep04-rag`          | RAG 表 `documents` / `document_chunks`（`011`） |
| 2026-05 | `ep03-data-storage` | 初版三表 ER |
