# MemoryOS 数据库设计

> **真相源**：Alembic 迁移（Story 3.2 `001_core_tables`）与 ORM 模型。  
> 本文描述 **Story 3.1** 约定；实现后若迁移有差异，以
> `apps/api/alembic/versions/` 为准。

**引擎**：PostgreSQL 16 · **扩展**：后续 EP04 可加 `pgvector`

---

##

```mermaid
erDiagram
    users ||--o{ conversations : owns
    conversations ||--o{ messages : contains

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
```

**删除策略**：`users` 删除 → 级联删除其 `conversations` → 级联删除其
`messages`。

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
| `title`      | `VARCHAR(500)` | NOT NULL, default `''`                      | 列表展示标题 |
| `created_at` | `TIMESTAMPTZ`  | NOT NULL, default `now()`                   |              |
| `updated_at` | `TIMESTAMPTZ`  | NOT NULL, default `now()`                   | 最后活动时间 |

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
| EP04   | `documents`、`chunks`、pgvector  |
| EP06   | 记忆相关表扩展                   |

---

## 变更记录

| 日期    | Change              | 说明        |
| :------ | :------------------ | :---------- |
| 2026-05 | `ep03-data-storage` | 初版三表 ER |
