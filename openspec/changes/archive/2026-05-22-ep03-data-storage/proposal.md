## Why

MemoryOS 的流式对话（EP02）、RAG 与鉴权都依赖持久化数据，但当前后端仅有健康检查，没有数据库与 ORM 层。需要在 EP02 之前完成 **PostgreSQL 基础设施** 与 **SQLAlchemy/Alembic 分层**，使会话与用户数据可存储、可迁移、可测试。

本 change **仅覆盖 EP03 Story 3.1 与 3.2**；Redis、JWT、索引优化（Story 3.3–3.5）留待后续 change。

## What Changes

- 新增 `infra/docker/docker-compose.yml`：本地 PostgreSQL 16（开发用），预留 Redis 服务定义占位或注释（本 change 不启用业务逻辑）。
- 新增 `docs/database.md`：ER 说明与 `users`、`conversations`、`messages` 表字段约定。
- 扩展 `apps/api`：`DATABASE_URL` 配置、异步 SQLAlchemy 2.0 engine、`get_db` 依赖注入。
- 新增 ORM Models 与 Alembic 首版迁移（创建三张核心表）。
- 新增 Repository + Service 骨架及 **最小 CRUD API**（例如用户/会话列表占位，供 Harness L1 与 EP02 衔接）。
- 更新 `requirements.txt`、`apps/api/.env.example`、`BE-engineering.md`。
- **不引入**：JWT 登录、Redis 缓存、pgvector（本 change 非目标）。

## Capabilities

### New Capabilities

- `postgres-infra`: 本地 Docker Compose 部署 PostgreSQL，连接串与文档。
- `core-schema`: 核心业务表 `users`、`conversations`、`messages` 的 schema 与 ER 文档。
- `data-access-layer`: 异步 SQLAlchemy、Alembic 迁移、Repository/Service 分层与 `Depends(get_db)`。

### Modified Capabilities

- （无）`openspec/specs/` 尚无既有 capability；health API 行为不变，仅新增数据层实现。

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `infra/docker/` | 新增 compose 与说明 |
| `apps/api/app/core/` | `config.py`、`database.py`（新） |
| `apps/api/app/models/` | ORM 模型 |
| `apps/api/app/repositories/` | 数据访问（新目录） |
| `apps/api/app/services/` | 业务 CRUD |
| `apps/api/app/api/v1/` | 新路由（如 `users`、`conversations` 只读列表） |
| `apps/api/alembic/` | 迁移目录 |
| `docs/database.md` | 新建 |
| 依赖 | `sqlalchemy[asyncio]`、`asyncpg`、`alembic` |
| EP02 | 依赖本 change 的 `messages` / `conversations` 模型 |
