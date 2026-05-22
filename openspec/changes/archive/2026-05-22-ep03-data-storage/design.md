## Context

- **现状**：`apps/api`
  已有 FastAPI 骨架（health、CORS、统一异常），`apps/api/app/models/`
  为空占位；`infra/docker` 仅有 README 占位。
- **约束**：Monorepo 根目录 `pnpm` 管前端；Python 在 Conda
  `memoryos-api`；API 响应格式 `{ code, message, data }`；分层 **Router →
  Service → Repository**。
- **范围**：Story 3.1（PostgreSQL + ER）+ Story 3.2（SQLAlchemy + Alembic +
  CRUD）；不含 Redis/JWT。

## Goals / Non-Goals

**Goals:**

- 开发者执行 `docker compose up -d postgres` 即可本地连库。
- `users`、`conversations`、`messages` 表通过 Alembic 可复现创建。
- API 可通过 `Depends(get_db)`
  访问异步 Session，完成基础 CRUD（至少会话/用户只读列表）。
- `docs/database.md` 与 ORM 字段一致；`pnpm test:api:harness`
  仍绿并新增 DB 相关 L1（可选 `/health` 扩展 db 状态）。

**Non-Goals:**

- Story 3.3 Redis、3.4 JWT、3.5 索引/事务优化（后续 change）。
- pgvector、LangGraph、SSE。
- 生产腾讯云部署（EP08）。

## Decisions

### D1: PostgreSQL 16 via Docker Compose

- **选择**：`infra/docker/docker-compose.yml` 单服务 `postgres`，端口
  `5432`，卷持久化 `postgres-data`。
- **理由**：与 EP08 编排一致；本地与 CI 可复用。
- **备选**：本机 Homebrew PostgreSQL — 环境差异大，不采用。

连接串（开发）：

```text
DATABASE_URL=postgresql+asyncpg://memoryos:memoryos@localhost:5432/memoryos
```

Compose 内服务名 `postgres`；API 在宿主机运行时用 `localhost`。

### D2: 表设计（对齐 EP02/EP03 命名）

| 表              | 主键      | 关键字段                                                               |
| :-------------- | :-------- | :--------------------------------------------------------------------- |
| `users`         | `id` UUID | `email` unique, `password_hash` nullable（JWT 前可空）, `created_at`   |
| `conversations` | `id` UUID | `user_id` FK, `title`, `created_at`, `updated_at`                      |
| `messages`      | `id` UUID | `conversation_id` FK, `role` enum/string, `content` text, `created_at` |

- 外键 `ON DELETE CASCADE`：`conversations` → `users`，`messages` →
  `conversations`。
- 时间戳：UTC，`server_default=now()`。

### D3: SQLAlchemy 2.0 async + asyncpg

- **选择**：`create_async_engine` + `async_sessionmaker` + `DeclarativeBase`。
- **`get_db`**：`async def get_db(): async with session.begin(): yield session`
  或 yield + `finally close`（无自动 commit 时每请求显式 commit）。

### D4: Alembic 异步迁移

- **选择**：`alembic init` 于 `apps/api/alembic/`，`env.py` 配置 async
  engine；首 revision `001_core_tables`。
- **理由**：团队可版本化 schema；与 BE-engineering 一致。

### D5: 目录布局

```text
apps/api/
├── alembic/
├── app/
│   ├── core/
│   │   ├── config.py      # + DATABASE_URL
│   │   └── database.py    # engine, session, get_db
│   ├── models/
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   └── message.py
│   ├── repositories/
│   │   ├── user_repository.py
│   │   └── conversation_repository.py
│   ├── services/
│   │   └── conversation_service.py
│   ├── schemas/
│   │   └── conversation.py  # Pydantic 列表项
│   └── api/v1/
│       └── conversations.py # GET list（占位）
```

路由内不写 SQL；Repository 仅数据访问。

### D6: 最小 API（Story 3.2 验收）

- `GET /api/v1/conversations?user_id=` — 列表（可先要求 query `user_id`
  测试，无 JWT）。
- `POST /api/v1/conversations` — 创建会话（body: `user_id`, `title`）。
- 可选：`POST /api/v1/users` 种子用户（dev only 或 migration seed）。

## Risks / Trade-offs

| 风险                           | 缓解                                                                 |
| :----------------------------- | :------------------------------------------------------------------- |
| Docker 未启动导致 API 启动失败 | 启动时 lazy connect；health 区分 db up/down；文档写明先 `compose up` |
| 异步 Session 泄漏              | `get_db` 统一 `yield` + `finally`                                    |
| 无 JWT 时 `user_id` 可伪造     | 本 change 接受；EP03.4 加鉴权                                        |
| Alembic 与 hand SQL 漂移       | 仅以 migration 为真相源，ER 文档引用 migration                       |

## Migration Plan

1. 合并前：Review `docs/database.md` + migration SQL。
2. 开发者：`docker compose up -d` → `alembic upgrade head` → `pnpm dev:api`。
3. 回滚：`alembic downgrade -1`；无生产数据时可直接 drop volume。

## Open Questions

- 是否在 compose 中一并启动 Redis 容器（**建议**：本 change 只启 postgres，Redis 注释占位）。
- `users.password_hash`：本 change 可 nullable，3.4 再必填。
