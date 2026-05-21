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
| 鉴权   | JWT                   | EP03                               |

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
│   │   ├── response.py      # 统一响应 { code, message, data }
│   │   └── exceptions.py    # AppException + 全局 handler
│   ├── schemas/             # Pydantic 模型（API 契约）
│   ├── models/              # SQLAlchemy ORM
│   └── services/            # 业务逻辑
├── requirements.txt
└── .env.example
```

---

## 3. 分层规范（目标形态）

```
HTTP Request
    ↓
api/v1/*.py          # 路由：参数解析、调用 Service、返回 ApiResponse
    ↓
services/*.py        # 业务：编排、事务边界
    ↓
models + Repository  # 数据访问（EP03）
```

**Story 1.4**：仅 `main` + `api` + `core` + `schemas`；`services` / `models`
为占位目录。

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

## 5. 本地开发

在 Monorepo **根目录**：

```bash
pnpm setup:api    # 首次
pnpm dev:api
pnpm dev:all      # 与前端并行
```

实现：`scripts/api.sh`（Conda `memoryos-api` 或 `apps/api/.venv`）。

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
| EP03  | `models/`、`DATABASE_URL`、JWT、`core/security.py` |
| EP02  | `api/v1/chat.py`、SSE、`services/chat.py`          |
| EP04+ | RAG、Agent、记忆 API                               |
