## Why

EP02–EP06 功能已在本地 `pnpm dev:stack` 跑通，但 **无容器化全栈路径**：无应用镜像、无 full Compose、无 Nginx SSE 反代。EP08（P0）交付 **Docker 多阶段镜像 + 本地 `docker compose --profile full` 一键全栈 + Nginx + 文档冒烟**；**不上云**——腾讯云 / SSL / 生产 CI 部署留 **EP14（K8s）**。

## What Changes

- **Story 8.1**：`apps/web`、`apps/api` 多阶段 Dockerfile；`.dockerignore`；非 root runtime 用户。
- **Story 8.2**：扩展 `infra/docker/docker-compose.yml` — `profiles: [full]` 增加 web、api、nginx；healthcheck + `depends_on`；`.env.docker.full.example`。
- **Story 8.3**：`infra/nginx/` — 本地 HTTP 反代；SSE（`proxy_buffering off`、长超时）；`/api/` → api、`/` → web。
- **Story 8.4**：`docs/tech/deployment.md` + `infra/docker/README.md` — 本地 full 启动、Alembic migrate、SSE 冒烟步骤。
- **Story 8.5**：本地 **Ollama** — LLM 与 Embedding **分离配置**（OpenAI 兼容）；宿主机 Ollama + Docker `host.docker.internal`；文档与 env 预设；Harness 仍 mock。
- **开发路径保留**：现有 `pnpm db:up` 仅 PG+Redis 仍可用；全栈为 opt-in `docker compose --profile full`。

**Non-Goals：**

- EP07 工作流、新业务功能
- 腾讯云、域名、SSL、安全组、生产 Secrets 运维
- GitHub Actions 镜像 build / deploy（→ EP14）
- TKE / Helm / K8s（→ EP14）
- 分布式 Compose profile（→ EP13）
- Playwright E2E on prod

## Capabilities

### New Capabilities

- `deployment-stack`: 应用 Dockerfile、本地 full Compose、Nginx 反代与 SSE、Compose env 模板、**Ollama 本地 LLM/Embedding**、本地部署文档

### Modified Capabilities

- `postgres-infra`: Compose 从「仅 PG+Redis」扩展为支持 **full profile**（web+api+nginx），开发默认行为不变

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/web/Dockerfile` · `next.config.ts` | standalone 输出 |
| `apps/api/Dockerfile` | uvicorn 入口 |
| `infra/docker/` | compose profiles、README、`.env.docker.full.example` |
| `infra/nginx/` | default.conf（本地 HTTP） |
| `docs/tech/deployment.md` | 本地 full stack 冒烟 |
| `docs/tech/ollama-local.md` | Ollama 安装与 LLM/Embed 配置 |
| `apps/api/app/core/config.py` | `embedding_api_base` 与 chat 分离 |
| `docs/tasks/epics/EP08-deployment.md` | Story 勾选 |
