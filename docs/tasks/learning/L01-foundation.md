# L01 — 基建阶段学习（第 1-2 周）

**对应史诗**：EP01 + EP03  
**建议时间分配**：学习 30% · 编码 70%  
**知识笔记**：[nextjs15.md](../../tech/knowledge/nextjs15.md) ·
[vite-vs-turbopack.md](../../tech/knowledge/vite-vs-turbopack.md) ·
[FE-engineering.md](../../tech/FE-engineering.md)

> 勾选：📖 能讲清 · 🔧 仓库已落地（写路径）

---

## 1. Next.js 15 + TypeScript 工程化

### 学什么

- [x] 📖 App Router：`app/` 目录即路由，`layout.tsx` 嵌套与复用
- [x] 📖 `page.tsx` / `loading.tsx` / `error.tsx` / `not-found.tsx` 职责区别
- [x] 📖 Server Component 默认 vs `'use client'`
      触发条件（Hook、事件、浏览器 API）
- [x] 📖 路径别名 `@/*` 与 Monorepo `workspace:*`、`transpilePackages`
- [ ] 📖 `transpileWorkspaces` 社区说法 vs `transpilePackages` 官方方案（见 [nextjs15 附录](../../tech/knowledge/nextjs15.md#附录-monorepo-编译--transpilepackages-与-transpileworkspaces)）
- [x] 📖 Turbopack（`next@15.5.18`）：dev `--turbopack`；生产默认 `next build`（Webpack），`next build --turbopack` 为 Beta
- [x] 📖 生产 `standalone`（Docker，EP08）
- [x] 🔧 `apps/web/`、`docs/tech/FE-engineering.md`
- [ ] 📖 `next/font`、Metadata API、环境变量 `NEXT_PUBLIC_*` 规则
- [ ] 🔧 能画出：浏览器请求 `/` → Next 渲染链路（简图即可）

### 面试常问

- App Router 和 Pages Router 核心区别？为什么新项目选 App Router？
- RSC 是什么？为什么能减小客户端 JS？Hydration 发生在什么时候？
- `NEXT_PUBLIC_` 和普通 env 有什么区别？能否在 RSC 里读私密 key？

### 实战易踩坑

| 坑                                   | 现象                  | 规避                                  |
| :----------------------------------- | :-------------------- | :------------------------------------ |
| 在 Server Component 里用 `useState`  | 编译/运行报错         | 拆到 Client 子组件并加 `'use client'` |
| 把 fetch 放在 Client 导致重复请求    | 闪屏、SEO 差          | 首屏数据放 RSC 或 layout 级 fetch     |
| Monorepo 改 `packages/shared` 不生效 | web 仍用旧代码        | 确认 `transpilePackages` 含包名 + 重启 dev |
| 误以为 Next 15 生产默认 Turbopack    | 面试说错              | **15.5** 生产默认 Webpack；**16** 才默认 Turbopack |
| 照抄 `transpileWorkspaces` 未验证     | 构建行为不确定        | 15.5 用稳定 `transpilePackages` 列表；见 nextjs15 附录对比 |
| `.env.local` 改了不生效              | 变量仍是旧值          | 改 env 必须重启 `next dev`            |
| 根目录与 `apps/web` 各装依赖         | lockfile 乱、幽灵依赖 | **只在仓库根** `pnpm install`         |

---

## 2. FastAPI 分层与依赖注入

### 学什么

- [ ] 📖 三层：Router（HTTP）→ Service（业务）→ Repository（数据访问）
- [ ] 📖 `async def` 路由 + `asyncpg` / SQLAlchemy 2.0 异步 Session
- [ ] 📖 `Depends(get_db)`、`Depends(get_current_user)` 组合与执行顺序
- [ ] 📖 Pydantic v2：`BaseModel`、`model_validate`、响应 `response_model`
- [ ] 📖 全局异常处理器、统一 `{ code, message, data }` 响应体
- [ ] 📖 CORS、请求 ID、日志中间件（结构化 log）
- [ ] 🔧 `apps/api/app/main.py`、`api/`、`core/`、`services/`、`repositories/`
- [ ] 🔧 `docs/tech/BE-engineering.md`

### 面试常问

- 为什么用 FastAPI 而不是 Flask/Django？异步带来的收益是什么？
- 依赖注入解决什么问题？和 Spring DI 的异同（能说一层即可）？
- 如何在 FastAPI 里保证事务边界（一个请求内 commit/rollback）？

### 实战易踩坑

| 坑                            | 现象                     | 规避                           |
| :---------------------------- | :----------------------- | :----------------------------- |
| 路由里直接写 SQL              | 难测、难复用             | 下沉 Repository                |
| 同步 ORM 阻塞事件循环         | QPS 上不去、延迟抖动     | 用 async engine + `await`      |
| `Depends` 里开 Session 不关闭 | 连接池耗尽               | `yield` + `finally close` 模式 |
| Pydantic 模型当 ORM 用        | 字段不一致踩坑           | ORM Model 与 Schema 分离       |
| 本地能跑、Docker 连不上 DB    | `localhost` 指向容器自身 | Compose 用服务名 `postgres`    |

---

## 3. PostgreSQL + SQLAlchemy + Alembic

### 学什么

- [ ] 📖 表设计：`users`、`conversations`（或 sessions）、`messages` 外键与级联
- [ ] 📖 索引：`(user_id)`、`(conversation_id, created_at)` 组合索引意义
- [ ] 📖 `EXPLAIN ANALYZE` 看 seq scan vs index scan（会认即可）
- [ ] 📖 Alembic：`revision` 链、`upgrade`/`downgrade`、勿手改已发布 migration
- [ ] 📖 连接池：`pool_size`、`max_overflow`、超时
- [ ] 📖 pgvector 扩展预置（EP04 用，可先 `CREATE EXTENSION`）
- [ ] 🔧 `alembic/versions/001_*.py`、`docs/database.md`

### 面试常问

- 为什么消息表要单独存 `role`/`content` 而不是 JSON 一大坨？
- 删除用户时会话和消息怎么处理？级联删除 vs 软删除 trade-off？
- 迁移线上失败如何回滚？多实例同时 migration 注意什么？

### 实战易踩坑

| 坑                        | 现象               | 规避                            |
| :------------------------ | :----------------- | :------------------------------ |
| 忘记 migration 就改 Model | 线上表结构不一致   | 改 Model 必生成 revision        |
| `String` 不设长度         | PostgreSQL 性能差  | 合理 `VARCHAR` / `Text`         |
| N+1 查询                  | 拉会话列表极慢     | `joinedload` / 批量查询         |
| 时区 naive datetime       | 时间差 8 小时      | 统一 UTC 存库                   |
| 开发库 migration 合并冲突 | 两人 revision 分叉 | 约定串行合并或 rebase migration |

---

## 4. Redis

### 学什么

- [ ] 📖 五种结构在本项目的可能用途：String（缓存）、Hash（会话元数据）、List（队列入门）
- [ ] 📖 TTL、缓存穿透/击穿/雪崩及**本项目可接受方案**（击穿用互斥或短期空值）
- [ ] 📖 Key 命名：`memoryos:session:{id}:meta`、`memoryos:ratelimit:{userId}`
- [ ] 📖 与 DB 一致性：Cache Aside（先更 DB 再删缓存）
- [ ] 🔧 `docker-compose` Redis + `core/redis.py` 封装

### 面试常问

- 会话列表放 Redis 还是 PG？什么情况下必须落库？
- Redis 和 PostgreSQL 数据不一致怎么办？

### 实战易踩坑

| 坑                          | 现象         | 规避                |
| :-------------------------- | :----------- | :------------------ |
| 无 TTL                      | 内存涨满     | 所有缓存 key 带 TTL |
| 把 Redis 当唯一数据源       | 重启丢会话   | 关键数据以 PG 为准  |
| `KEYS *` 生产使用           | Redis 卡顿   | 用 `SCAN`           |
| 序列化 ORM 对象直接进 Redis | 反序列化失败 | 存 DTO/JSON         |

---

## 5. JWT 鉴权

### 学什么

- [ ] 📖 Access Token vs Refresh Token 分工、过期时间策略
- [ ] 📖 `Authorization: Bearer`、FastAPI `HTTPBearer` 依赖
- [ ] 📖 密码：bcrypt/argon2，禁止明文
- [ ] 📖 前端：Token 存哪（httpOnly Cookie vs localStorage）与安全 trade-off
- [ ] 🔧 `POST /auth/login`、`GET /me`、受保护路由依赖

### 面试常问

- JWT 无状态优缺点？如何实现登出（黑名单）？
- 如何在 SSE 长连接里传递鉴权？

### 实战易踩坑

| 坑                     | 现象              | 规避                |
| :--------------------- | :---------------- | :------------------ |
| JWT secret 写死在代码  | 泄露全站失守      | 环境变量 + 轮换策略 |
| 只校验签名不校验 `exp` | 过期 token 仍可用 | 完整校验 claims     |
| CORS `*` + Cookie 鉴权 | 跨站风险          | 白名单 origin       |
| SSE 未带 Token         | 401 但页面无提示  | 统一 401 拦截跳登录 |

---

## 6. Git 与协作规范

- [x] 📖 分支：`feat/*`、`fix/*`；Conventional Commits；`feat(web)` /
      `feat(api)` scope
- [x] 🔧 `CONTRIBUTING.md`、`.editorconfig`
- [ ] 📖 PR 自检：`pnpm lint`、迁移可执行、无 `.env` 泄露

### 实战易踩坑

| 坑                         | 现象     | 规避              |
| :------------------------- | :------- | :---------------- |
| 提交 `.env`                | 密钥泄露 | 仅 `.env.example` |
| 巨大 `node_modules` 进 Git | 仓库膨胀 | 靠 `.gitignore`   |
| 前后端各搞一套 commit 规范 | 难追溯   | 统一 CONTRIBUTING |

---

## 本周最小闭环

1. EP01 Story 1.4：FastAPI `GET /health` + 分层目录
2. EP03：表结构 + Alembic 首版迁移 + Redis 容器
3. `BE-engineering.md` 初版（含分层图 + 与 FE 协作边界）

## 阶段自测（口述 5 分钟）

- [ ] Monorepo 目录职责 + 前后端如何联调
- [ ] 一条消息从写入 PG 到读出经过哪些层
- [ ] 说清 2 个本阶段踩坑及你的修复方式
