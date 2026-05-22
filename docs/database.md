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
| `password_hash` | `VARCHAR(255)` | NULL                            | bcrypt 哈希；Story 3.1 可空 |
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

**索引（Story 3.5 优化）**：`(user_id, updated_at DESC)`
— 会话列表；本 Story 可在迁移中加基础索引。

---

## 表：`messages`

| 列                | 类型          | 约束                                                | 说明                                                       |
| :---------------- | :------------ | :-------------------------------------------------- | :--------------------------------------------------------- |
| `id`              | `UUID`        | PK                                                  | 消息 ID                                                    |
| `conversation_id` | `UUID`        | FK → `conversations.id` ON DELETE CASCADE, NOT NULL |                                                            |
| `role`            | `VARCHAR(32)` | NOT NULL                                            | `user` / `assistant` / `system`（EP02 流式写入 assistant） |
| `content`         | `TEXT`        | NOT NULL                                            | 正文                                                       |
| `created_at`      | `TIMESTAMPTZ` | NOT NULL, default `now()`                           | 排序依据                                                   |

**索引（Story 3.5）**：`(conversation_id, created_at)` — 拉取历史。

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
| 启动         | `cd infra/docker && docker compose up -d`                        |

详见 [infra/docker/README.md](../infra/docker/README.md)。

---

## 后续史诗（不在 Story 3.1–3.2）

| 史诗   | 表/能力                         |
| :----- | :------------------------------ |
| EP03.3 | Redis 会话列表缓存              |
| EP03.4 | JWT、`users.password_hash` 必填 |
| EP04   | `documents`、`chunks`、pgvector |
| EP06   | 记忆相关表扩展                  |

---

## 变更记录

| 日期    | Change              | 说明        |
| :------ | :------------------ | :---------- |
| 2026-05 | `ep03-data-storage` | 初版三表 ER |
