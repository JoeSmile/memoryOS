# EP03 — 数据存储层搭建

| 属性         | 值                                                                                                                                                           |
| :----------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **周期**     | 第 1-2 周（与 EP01 并行）                                                                                                                                    |
| **优先级**   | P0                                                                                                                                                           |
| **状态**     | 🟡 进行中（3.1–3.4 完成，3.5 待做）                                                                                                                          |
| **OpenSpec** | 进行中 [`ep03-db-optimize`](../../../openspec/changes/ep03-db-optimize/)（**EP02 Program Phase 1**）· 已归档 [`ep03-jwt`](../../../openspec/changes/archive/2026-05-22-ep03-jwt/) · [`ep03-redis`](../../../openspec/changes/archive/2026-05-22-ep03-redis/) |
| **学习路线** | [L01-foundation.md](../learning/L01-foundation.md) · [L00](../learning/L00-ai-collab-stack.md)                                                               |

---

## Story 3.1 PostgreSQL

- [x] 本地 + 线上 PostgreSQL 部署（Docker Compose）— 本地
      `infra/docker/docker-compose.yml`
- [x] 设计表：`users`、`conversations`、`messages`（对齐 project-description 命名）— 见
      `docs/database.md`
- [x] ER 文档 `docs/database.md`

## Story 3.2 SQLAlchemy + Alembic

- [x] 异步引擎 `asyncpg` + ORM Models
- [x] Alembic 初始化与首版迁移（`pnpm db:migrate`）
- [x] Repository / Service 层 CRUD +
      `GET|POST /api/v1/conversations`、`POST /api/v1/users`

## Story 3.3 Redis

- [x] Docker Redis 7
- [x] 会话列表缓存、流式临时缓存
- [ ] 可选：JWT refresh / 黑名单（留 Story 3.4）

## Story 3.4 JWT 鉴权

- [x] 注册 / 登录、bcrypt
- [x] Bearer 中间件、`GET /me`
- [x] 前端登录/注册页 + Token 拦截器（`/login`、`/register`、`lib/api-client.ts`）

## Story 3.5 优化

- [x] 业务索引、`user_id` / `conversation_id` 外键
- [x] 事务：创建会话 + 首条消息
- [x] 慢查询与连接池调优（基础）

---

## 同步学习

- [ ] [L00](../learning/L00-ai-collab-stack.md) OpenSpec 本变更 propose →
      archive
- [ ] SQLAlchemy ORM 高阶用法（理解 / 落地）
- [ ] Alembic 迁移流程（理解 / 落地）
- [ ] Redis 过期策略与会话缓存设计（理解 / 落地）
- [ ] JWT 原理与刷新令牌（理解 / 落地）
