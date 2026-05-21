# EP01 — 项目工程架构初始化

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 1-2 周 |
| **优先级** | P0 |
| **状态** | 🟡 进行中 |
| **学习路线** | [L01-foundation.md](../learning/L01-foundation.md) |
| **目标文档** | [FE-engineering.md](../../tech/FE-engineering.md) ✅ · [BE-engineering.md](../../tech/BE-engineering.md) ✅ |

---

## Story 1.1 Monorepo 目录结构

- [x] 搭建 `memoryos` 根目录 + `apps/web`、`apps/api`、`packages`、`infra`
- [x] 根目录 `package.json` + `pnpm-workspace.yaml`
- [x] 各子包 `README.md`

## Story 1.2 Git 与开源规范

- [x] 初始化 Git、`.gitignore`
- [x] 根目录 `README.md`、`LICENSE`（MIT）
- [x] `.editorconfig`、`CONTRIBUTING.md`

## Story 1.3 Next.js 15 前端初始化

- [x] `create-next-app`：App Router、TS、Tailwind v4
- [x] 路径别名 `@/*`、`eslint` + `prettier`
- [x] `.env.example`、`layout` / `page` / `not-found`
- [x] `pnpm dev:web` 可启动

## Story 1.4 FastAPI 后端初始化

- [x] Python 虚拟环境 + `requirements.txt` / `pyproject.toml`
- [x] 目录：`app/main.py`、`api/`、`core/`、`models/`、`schemas/`
- [x] `GET /health`、CORS、全局异常、统一响应
- [x] `.env.example`、`uvicorn` 本地可启动

## Story 1.5 统一规范

- [x] 前端工程说明（FE-engineering）
- [x] 后端工程说明（BE-engineering）初稿
- [ ] 分层规范：路由 → Service → Repository
- [ ] Conventional Commits（CONTRIBUTING 已写，可选 Husky）

---

## 同步学习（详见 L01）

- [x] Next.js 15 + TS 工程化（理解） · [x] 落地 `apps/web`
- [x] FastAPI 分层与依赖注入（理解） · [python-getting-started.md](../../tech/python-getting-started.md)
- [x] FastAPI 分层与依赖注入（落地 `apps/api`）
- [ ] PostgreSQL 建表与索引（理解）
- [ ] Redis 业务场景（理解）
- [x] Git 分支与提交规范（理解） · [x] 落地 `CONTRIBUTING.md`
