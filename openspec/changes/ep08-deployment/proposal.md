## Why

EP02–EP06 已在 `pnpm dev:stack` 跑通，但 **无统一部署契约**：无标准镜像、无与环境无关的配置 schema、本地打出来的包与上云脱节。EP08 交付 **可复用的 web/api 镜像 + Compose full 本地冒烟 + 环境 Profile（local / cloud）+ CI 构建镜像**；本地目的是 **验证流程与参数**，验证通过后 **同一镜像与同一套 env 键** 推到 registry，在 VM Compose 或 EP14 K8s 上运行——**不在 EP08 重做第二套打包**。

## What Changes

- **Story 8.1**：`apps/web`、`apps/api` 多阶段 Dockerfile（**云上复用同一 Dockerfile**）。
- **Story 8.2**：Compose `profiles: [full]`；镜像 tag 可配置（`WEB_IMAGE` / `API_IMAGE`）；**`.env.deployment.example`** 含 `local` / `cloud` 两套取值说明。
- **Story 8.3**：`infra/nginx/` — HTTP 反代 + SSE（本地与云上 Nginx/Ingress 配置同源）。
- **Story 8.4**：`docs/tech/deployment.md` — **本地验证清单** + **上云晋级清单**（推镜像、换 profile、托管 PG/Redis、域名）。
- **Story 8.5**：**local profile** Ollama（`qwen3:8b` + embed）；**cloud profile** 用云 LLM（百炼等），**env 键不变、只换值**。
- **Story 8.6**：GitHub Actions **构建 web/api 镜像**（`docker build`）；有 registry secret 可 push；与本地 build 同一 Dockerfile。
- **开发路径保留**：默认 `docker compose up` 仍仅 PG+Redis。

**Non-Goals：**

- EP07 工作流、新业务功能
- TKE / Helm 编排实现（→ EP14，但 **消费 EP08 镜像**）
- Terraform 全自动购云资源
- Ollama 进 Compose / 上云 GPU 推理（cloud 用 API Key）

## Capabilities

### New Capabilities

- `deployment-stack`: 可晋级镜像、Compose full、Nginx SSE、**部署 env 契约**（local/cloud profile）、Ollama local、CI 镜像 build

### Modified Capabilities

- `postgres-infra`: full profile；cloud 时 DB/Redis 可指向托管实例（仅 env 变更）

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/web/Dockerfile` · `apps/api/Dockerfile` | 本地与云 **同一镜像** |
| `infra/docker/` | compose、`.env.deployment.example`、README |
| `infra/nginx/` | 本地 Nginx；云 Ingress 对照表 |
| `docs/tech/deployment.md` | local 冒烟 + cloud 晋级 |
| `.github/workflows/deploy.yml` | 镜像 build（+ 可选 push） |
| `apps/api/app/core/config.py` | `embedding_api_base` |
| `docs/tasks/epics/EP08-deployment.md` | Story 8.1–8.6 |
