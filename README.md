# MemoryOS

面向生产实践的 **AI 记忆与知识平台**：流式对话、RAG 知识库、LLM Agent 工具调度、多层级记忆与工作流编排，采用 Monorepo 统一工程管理。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Node](https://img.shields.io/badge/node-%3E%3D20-brightgreen)](./package.json)
[![pnpm](https://img.shields.io/badge/pnpm-9.x-orange)](./pnpm-workspace.yaml)

## 特性（规划 / 进行中）

- **流式对话** — SSE 全链路流式输出，多轮会话管理
- **RAG 知识库** — 文档解析、切块、Embedding、pgvector 召回与溯源引用
- **Agent 智能体** — Function Calling、ReAct、内置工具编排
- **记忆体系** — 短期滑动窗口 + 长期用户画像 + 上下文摘要压缩
- **工程化部署** — Docker、Nginx、腾讯云、GitHub Actions CI/CD

> 当前处于 **EP01 工程初始化** 阶段，开发任务与学习路线见 [docs/tasks](./docs/tasks/README.md)。

## 技术栈

### 前端

| 类别 | 技术 |
|:-----|:-----|
| 框架 | Next.js 15、React、TypeScript |
| 样式 | TailwindCSS |
| 规范 | ESLint、Prettier、App Router |
| 状态 | Zustand |
| 渲染 | react-markdown（代码高亮 / GFM） |
| 流式 | ReadableStream / SSE 客户端 |

### 后端

| 类别 | 技术 |
|:-----|:-----|
| 框架 | FastAPI、Uvicorn |
| 模型 | Pydantic v2 |
| 鉴权 | JWT |
| 通信 | SSE 流式推送 |
| LLM | OpenAI SDK / 兼容接口 |

### 数据与 AI

| 类别 | 技术 |
|:-----|:-----|
| 数据库 | PostgreSQL、SQLAlchemy、Alembic |
| 向量 | pgvector |
| 缓存 | Redis |
| RAG | 文档解析、切块、Embedding、相似度召回 |
| Agent | Function Calling、ReAct、工具编排 |

### 运维

Docker · Docker Compose · Nginx · 腾讯云 · GitHub Actions

## 目录结构

```
memoryOS/
├── apps/
│   ├── web/          # Next.js 15 前端
│   └── api/          # FastAPI 后端（Python）
├── packages/
│   ├── shared/       # 共享类型、常量、工具
│   └── ui/           # 公共 React 组件
├── infra/
│   ├── docker/       # 容器与 Compose（EP08）
│   └── nginx/        # 反向代理配置（EP08）
├── docs/             # 项目文档与任务计划
├── package.json      # Monorepo 根脚本
└── pnpm-workspace.yaml
```

各子目录均有独立 `README.md`，说明职责与启动方式。

## 快速开始

### 前置要求

- [Node.js](https://nodejs.org/) >= 20
- [pnpm](https://pnpm.io/) 9.x
- [Python](https://www.python.org/) >= 3.11（后端，Story 1.4 起）
- [Docker](https://www.docker.com/)（数据库，EP03 起，可选）

### 安装依赖

在**仓库根目录**执行（不要进子目录单独 `npm install`）：

```bash
git clone https://github.com/<your-org>/memoryOS.git
cd memoryOS

# 前端 + packages（pnpm workspace）
pnpm install

# 后端 Python（首次或 requirements.txt 变更后）
pnpm setup:api
# 一键：pnpm install:all
```

| 范围 | 命令 | 说明 |
|:-----|:-----|:-----|
| JS/TS 全仓 | `pnpm install` | 只装 `apps/web`、`packages/*`（见 `pnpm-workspace.yaml`） |
| Python API | `pnpm setup:api` | Conda 环境 `memoryos-api` 或 `apps/api/.venv` + pip |
| 给某子包加依赖 | `pnpm --filter @memoryos/web add zustand` | 依赖写在子包 `package.json` |
| 给 shared 加依赖 | `pnpm --filter @memoryos/shared add lodash-es` | 同上 |

> `apps/api` 是 Python 项目，**不在** pnpm workspace；用根脚本 `setup:api` / `dev:api` 即可。  
> 已有 Conda 环境 `memoryos-api` 时，日常只需 `pnpm dev:api`（不必每次 `conda activate`）。  
> 多子包共用 npm 包：各子包须在各自 `package.json` 声明，或集中在 `packages/ui`；详见 [FE-engineering.md §2](./docs/tech/FE-engineering.md#2-monorepopnpm-workspace)。

### 启动开发服务（均在根目录）

```bash
pnpm dev:web    # http://localhost:3000
pnpm dev:api    # http://localhost:8000/docs
pnpm dev:all    # 前后端并行
pnpm test:api:harness   # API 契约测试（Harness L1）
```

使用 Conda 时无需每次 `conda activate`：`dev:api` 会通过 `conda run -n memoryos-api` 启动。

**AI 协作栈**（带队可复用）：[入门](./docs/tech/ai-collab-stack.md) · [最佳实践](./docs/tech/ai-collab-best-practices.md) · [团队 onboarding](./docs/team/onboarding.md) · [EP00](./docs/tasks/epics/EP00-ai-collaboration.md) · [L00](./docs/tasks/learning/L00-ai-collab-stack.md)

### 环境变量

| 应用 | 模板文件 | 说明 |
|:-----|:---------|:-----|
| Web | `apps/web/.env.example` | `NEXT_PUBLIC_API_URL` 等 |
| API | `apps/api/.env.example` | 数据库、Redis、OpenAI Key 等 |

复制对应 `.env.example` 为 `.env` / `.env.local` 后填写，**切勿提交真实密钥**。

## 开发脚本

| 命令 | 说明 |
|:-----|:-----|
| `pnpm install` | 安装 workspace（web + packages） |
| `pnpm setup:api` | 安装 API Python 依赖，生成 `.env` |
| `pnpm install:all` | `install` + `setup:api` |
| `pnpm dev:web` | 启动前端 |
| `pnpm dev:api` | 启动后端（需先 `setup:api`） |
| `pnpm dev:all` | 前后端并行 |
| `pnpm build` | 构建所有 workspace 包 |
| `pnpm lint` | 运行各包 lint |
| `pnpm format` | 运行各包格式化 |
| `pnpm test:api:harness` | API Harness L1 测试 |

## 路线图

详见 [docs/tasks](./docs/tasks/README.md)（史诗任务 + 同步学习路线 + 周度复盘）。

| 阶段 | 史诗 | 目标 |
|:----:|:-----|:-----|
| 1–2 周 | EP01 + EP03 | 工程初始化 + 数据层 |
| 第 3 周 | EP02 | 流式对话 |
| 4–5 周 | EP04 | RAG 知识库 |
| 第 6 周 | EP05 | Agent 工具调度 |
| … | … | … |

## 贡献

欢迎提交 Issue 与 Pull Request，请先阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)。

- 分支：`feat/*`、`fix/*`、`docs/*`
- 提交：遵循 [Conventional Commits](https://www.conventionalcommits.org/)

## 许可证

本项目采用 [MIT License](./LICENSE) 开源。
