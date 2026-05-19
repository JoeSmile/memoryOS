# apps/api — 后端 API 服务

基于 **FastAPI** 的异步 REST / SSE 服务，承载对话、RAG、Agent、记忆等核心能力。

## 技术栈

- 框架：FastAPI + Uvicorn
- 数据模型：Pydantic v2
- ORM：SQLAlchemy + Alembic
- 数据库：PostgreSQL + pgvector
- 缓存：Redis
- 鉴权：JWT
- LLM：OpenAI SDK / 通用兼容接口

## 目录约定（Story 1.4 初始化后）

```
apps/api/
├── app/
│   ├── main.py           # 应用入口
│   ├── api/              # 路由（v1/chat, knowledge, auth…）
│   ├── core/             # 配置、安全、依赖注入
│   ├── models/           # SQLAlchemy ORM
│   ├── schemas/          # Pydantic 模型
│   └── services/         # 业务逻辑
├── alembic/              # 数据库迁移
├── requirements.txt
└── .env.example
```

## 启动

```bash
cd apps/api

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env        # 编辑数据库、Redis、OpenAI 等配置

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API 文档：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/health>（Story 1.4）

> 本包为 Python 项目，**不纳入** pnpm workspace；与前端通过 HTTP / SSE 通信。
