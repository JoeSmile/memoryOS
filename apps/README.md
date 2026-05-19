# apps — 业务应用层

本目录存放 MemoryOS 的可独立部署业务应用。

| 目录 | 技术栈 | 说明 |
|:-----|:-------|:-----|
| [`web/`](./web/) | Next.js 15 + React + TypeScript + TailwindCSS | 前端 Web 应用 |
| [`api/`](./api/) | FastAPI + Python | 后端 API 服务 |

## 启动方式（初始化完成后）

```bash
# 前端（仓库根目录）
pnpm dev:web

# 后端
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

> Story 1.3 / 1.4 将完成 Next.js 与 FastAPI 的完整初始化。
