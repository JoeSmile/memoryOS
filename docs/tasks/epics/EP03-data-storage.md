# EP03 — 数据存储层搭建

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 1-2 周（与 EP01 并行） |
| **优先级** | P0 |
| **状态** | ⚪ 待开始 |
| **学习路线** | [L01-foundation.md](../learning/L01-foundation.md) · [L00](../learning/L00-ai-collab-stack.md) |
| **OpenSpec** | 建议 change：`ep03-data-storage`（先 [EP00](./EP00-ai-collaboration.md) Story 0.1–0.3） |

---

## Story 3.1 PostgreSQL

- [ ] 本地 + 线上 PostgreSQL 部署（Docker Compose）
- [ ] 设计表：`users`、`conversations`、`messages`（对齐 project-description 命名）
- [ ] ER 文档 `docs/database.md`

## Story 3.2 SQLAlchemy + Alembic

- [ ] 异步引擎 `asyncpg` + ORM Models
- [ ] Alembic 初始化与首版迁移
- [ ] Repository / Service 层 CRUD

## Story 3.3 Redis

- [ ] Docker Redis 7
- [ ] 会话列表缓存、流式临时缓存
- [ ] 可选：JWT refresh / 黑名单

## Story 3.4 JWT 鉴权

- [ ] 注册 / 登录、bcrypt
- [ ] Bearer 中间件、`GET /me`
- [ ] 前端登录页 + Token 拦截器

## Story 3.5 优化

- [ ] 业务索引、`user_id` / `conversation_id` 外键
- [ ] 事务：创建会话 + 首条消息
- [ ] 慢查询与连接池调优（基础）

---

## 同步学习

- [ ] [L00](../learning/L00-ai-collab-stack.md) OpenSpec 本变更 propose → archive
- [ ] SQLAlchemy ORM 高阶用法（理解 / 落地）
- [ ] Alembic 迁移流程（理解 / 落地）
- [ ] Redis 过期策略与会话缓存设计（理解 / 落地）
- [ ] JWT 原理与刷新令牌（理解 / 落地）
