# MemoryOS 后端工程说明

> EP01 Story 1.5 初稿；随 EP03（数据库）、EP02（SSE）持续补充。

---

## 1. 技术栈

| 层级   | 选型                  | 说明                               |
| :----- | :-------------------- | :--------------------------------- |
| 运行时 | Python 3.11+          | 与 LangGraph / LlamaIndex 生态一致 |
| Web    | FastAPI + Uvicorn     | 异步、自动 OpenAPI                 |
| 校验   | Pydantic v2           | Request/Response + Settings        |
| ORM    | SQLAlchemy + Alembic  | EP03 落地                          |
| 数据库 | PostgreSQL + pgvector | EP03                               |
| 缓存   | Redis                 | EP03                               |
| 鉴权   | JWT (PyJWT + bcrypt)  | EP03 Story 3.4 ✅                  |

Python 零基础入门见 [python-getting-started.md](./python-getting-started.md)。

---

## 2. 目录结构

```
apps/api/
├── app/
│   ├── main.py              # FastAPI 实例、中间件、全局异常
│   ├── api/
│   │   └── v1/
│   │       ├── router.py    # 聚合 v1 路由
│   │       └── health.py    # 健康检查
│   ├── core/
│   │   ├── config.py        # 环境变量（pydantic-settings）
│   │   ├── database.py      # async engine、get_db
│   │   ├── security.py      # bcrypt、JWT 签发/校验
│   │   ├── deps.py          # get_current_user（Bearer）
│   │   ├── response.py      # 统一响应 { code, message, data }
│   │   └── exceptions.py    # AppException + 全局 handler
│   ├── schemas/             # Pydantic 模型（API 契约）
│   ├── models/              # SQLAlchemy ORM（User, Conversation, Message）
│   ├── repositories/        # 数据访问（EP03 §4）
│   └── services/            # 业务逻辑
├── alembic/                 # 迁移；revision 001_core_tables
├── alembic.ini
├── requirements.txt
└── .env.example
```

---

## 3. 分层规范（目标形态）

> 可审查代码细则（函数粒度、diff 预算、注释）：[code-quality.md](./code-quality.md)

```
HTTP Request
    ↓
api/v1/*.py          # 路由：参数解析、调用 Service、返回 ApiResponse
    ↓
services/*.py        # 业务：编排、事务边界
    ↓
models + Repository  # 数据访问（EP03）
```

**Story 3.2（EP03）**：`database.py`、`models/`、`repositories/`、`services/`、`api/v1/users` + `conversations`、`alembic/`。

---

## 4. 统一响应

成功：

```json
{
  "code": 0,
  "message": "ok",
  "data": { "status": "ok", "app": "MemoryOS API", "env": "development" }
}
```

业务错误（`AppException`）：

```json
{
  "code": 40001,
  "message": "描述信息",
  "data": null
}
```

HTTP 状态码与 `code` 可分离：例如鉴权失败 HTTP 401，`code` 为业务码。

---

## 4.1 JWT 鉴权（Story 3.4）

| 路由 | 说明 |
|:-----|:-----|
| `POST /api/v1/auth/register` | 注册，`password` 写入 `users.password_hash`（bcrypt） |
| `POST /api/v1/auth/login` | 登录，返回 `{ access_token, token_type: "bearer" }` |
| `GET /api/v1/me` | 需 `Authorization: Bearer <token>`，返回当前用户 |

**环境变量**（`apps/api/.env.example`）：`JWT_SECRET`、`JWT_ALGORITHM`（默认 HS256）、`ACCESS_TOKEN_EXPIRE_MINUTES`、`PASSWORD_MIN_LENGTH`。

**实现要点**：

- `app/core/security.py`：`hash_password` / `verify_password`、`create_access_token` / `decode_access_token`；payload `{ sub: user_uuid, exp }`。
- `app/core/deps.py`：`get_current_user` 解析 Bearer，失败 `401` + `code` 40101。
- `POST /api/v1/users` 保留供 harness/开发，**deprecated**（无密码快捷建用户）。

**业务码**：`40101` 未认证/无效 token · `40102` 登录凭证错误 · `40901` 邮箱已存在 · `42901` 限流超限 · `42902` 日 Token 配额用尽 · `50301` JWT 未配置（`JWT_SECRET` 缺失时 login/me）· `50302` 限流依赖 Redis 不可用且 fail-closed。

**前端**：`apps/web/lib/api-client.ts` 自动附加 Bearer；已登录时 HTTP 401 清 `localStorage` 的 `memoryos_access_token` 并跳转 `/login`（首版 localStorage，EP09 可改 httpOnly）。

---

## 5. 本地开发

在 Monorepo **根目录**：

```bash
pnpm setup:api    # 首次
pnpm dev:api
pnpm dev:all      # 与前端并行
```

实现：`scripts/api.sh`（Conda `memoryos-api` 或 `apps/api/.venv`）。

数据库迁移（EP03 Story 3.2）：

```bash
pnpm db:up && pnpm db:migrate
```

| 地址                                | 说明        |
| :---------------------------------- | :---------- |
| http://localhost:8000/health        | 健康检查    |
| http://localhost:8000/api/v1/health | v1 同名接口 |
| http://localhost:8000/docs          | Swagger     |

前端 `apps/web` 默认 `localhost:3000`，CORS 已在 `.env.example` 配置。

---

## 6. 与 Monorepo 的关系

- `apps/api` **不**加入 pnpm workspace，独立 Python 虚拟环境。
- 与 `apps/web` 通过 HTTP / SSE 通信；共享类型后续可放
  `packages/shared`（仅 TS）或 OpenAPI 生成客户端。

---

## 7. 后续 Epic 落点

| Epic  | 后端增量                                           |
| :---- | :------------------------------------------------- |
| EP03  | `models/`、`DATABASE_URL`、JWT、`core/security.py`、`auth` + `GET /me` |
| EP02  | `api/v1/chat.py`、SSE、`services/chat.py`          |
| EP04+ | RAG、Agent、记忆 API                               |
