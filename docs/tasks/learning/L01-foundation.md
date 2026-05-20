# L01 — 基建阶段学习（第 1-2 周）

**对应史诗**：EP01 + EP03  
**建议时间分配**：学习 30% · 编码 70%

---

## 1. Next.js 15 + TypeScript 工程化

- [x] 📖 App Router 与项目目录职责
- [x] 🔧 落地：`apps/web/`、`docs/tech/FE-engineering.md`
- [ ] 📖 Server / Client Component 边界（预研，EP02 要用）
- [ ] 📖 Monorepo 下 workspace 依赖与 `transpilePackages`

**自测**：能说明 `pnpm dev:web` 到页面渲染的链路。

---

## 2. FastAPI 分层与依赖注入

- [ ] 📖 路由 / Service / Repository 三层职责
- [ ] 📖 `Depends()` 与异步依赖注入
- [ ] 🔧 落地：`apps/api/app/` 分层骨架
- [ ] 🔧 落地：`docs/tech/BE-engineering.md`（待写）

**自测**：能写一个带 DB Session 依赖的 `GET /health` 变体。

---

## 3. PostgreSQL

- [ ] 📖 `users` / `conversations` / `messages` 表关系与范式
- [ ] 📖 常用索引、EXPLAIN 初识
- [ ] 🔧 落地：`docs/database.md` + Alembic 迁移

**自测**：能画出 ER 图并解释级联删除策略。

---

## 4. Redis

- [ ] 📖 缓存穿透/击穿/雪崩（概念级）
- [ ] 📖 会话列表缓存、流式中间态 key 设计
- [ ] 🔧 落地：Docker Compose 中 Redis + 封装客户端

---

## 5. Git 与协作

- [x] 📖 分支模型、Conventional Commits
- [x] 🔧 落地：`CONTRIBUTING.md`、`.editorconfig`

---

## 本周最小闭环（建议）

1. 完成 EP01 Story 1.4（FastAPI 可启动）  
2. 完成 EP03 Story 3.1–3.2（表 + 迁移）  
3. 写出 `BE-engineering.md` 初版（≥ 300 字）
