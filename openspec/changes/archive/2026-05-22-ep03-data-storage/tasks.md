## 1. Story 3.1 — PostgreSQL 与文档（EP03）

- [x] 1.1 新增 `infra/docker/docker-compose.yml`（postgres:16、volume、healthcheck、默认库/用户/密码）
- [x] 1.2 更新 `infra/docker/README.md`：启动命令、`DATABASE_URL`、与 `pnpm dev:api` 的配合
- [x] 1.3 编写 `docs/database.md`：ER 图（mermaid 或文字）、`users` / `conversations` / `messages` 字段说明
- [x] 1.4 扩展 `apps/api/.env.example` 增加 `DATABASE_URL`（与 compose 一致）
- [x] 1.5 本地验证：`docker compose up -d` 后 `psql` 或容器内可连库

## 2. Story 3.2 — 依赖与数据库核心模块

- [x] 2.1 `requirements.txt` 增加 `sqlalchemy[asyncio]`、`asyncpg`、`alembic`
- [x] 2.2 新增 `app/core/database.py`：`create_async_engine`、`async_sessionmaker`、`get_db`（yield + close）
- [x] 2.3 扩展 `app/core/config.py`：读取 `DATABASE_URL`，缺省时开发环境可警告
- [x] 2.4 新增 `app/models/base.py` 与 `user` / `conversation` / `message` ORM 模型（UUID 主键、FK、时间戳）

## 3. Story 3.2 — Alembic 迁移

- [x] 3.1 在 `apps/api` 执行 `alembic init`，配置 `alembic.ini` 与 `env.py`（async）
- [x] 3.2 生成首版 revision `001_core_tables` 创建三张表
- [x] 3.3 文档补充：`alembic upgrade head` / `downgrade` 命令（`infra/docker/README` 或 `apps/api/README`）
- [x] 3.4 本地验证：空库 `upgrade head` 后表存在

## 4. Story 3.2 — Repository / Service / API

- [x] 4.1 新增 `app/repositories/user_repository.py`、`conversation_repository.py`（基础 CRUD）
- [x] 4.2 新增 `app/services/conversation_service.py`（创建会话、按 user 列表）
- [x] 4.3 新增 Pydantic schemas：`ConversationCreate`、`ConversationRead` 等
- [x] 4.4 新增 `app/api/v1/conversations.py`：`GET` 列表、`POST` 创建；注册到 `router.py`
- [x] 4.5 可选：`POST /api/v1/users` 或 Alembic seed 脚本，便于手动测试

## 5. 测试、文档与收尾

- [x] 5.1 扩展 Harness L1：对话 API 返回统一 envelope；非法 `user_id` 返回 422/404
- [x] 5.2 运行 `pnpm test:api:harness` 全部通过
- [x] 5.3 更新 `docs/tech/BE-engineering.md`：database、models、repositories、alembic 路径
- [x] 5.4 勾选 `docs/tasks/epics/EP03-data-storage.md` Story 3.1、3.2
- [x] 5.5 合并后执行 `/opsx:archive` 并勾选 L00 OpenSpec 相关学习项

## 6. 明确不在本 change（勿做）

- [ ] 6.1 （确认跳过）Redis 业务缓存 — Story 3.3
- [ ] 6.2 （确认跳过）JWT / 登录 / `GET /me` — Story 3.4
- [ ] 6.3 （确认跳过）业务索引优化、事务专项 — Story 3.5
