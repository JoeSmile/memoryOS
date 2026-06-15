## Context

- **现状**：Dockerfile 已在 Story 8.1 落地；Compose 仍仅 PG+Redis；无统一「部署 env」；用户需 **本地验证参数 → 原样上云**，而非两套打包。
- **约束**：Harness 仍 mock；`pnpm db:up` 默认行为不变；SSE 经 Nginx 必须可用。
- **依赖**：EP03 schema、EP02 SSE。

## Goals / Non-Goals

**Goals:**

- **一套镜像**：`memoryos-web` / `memoryos-api`，本地 `docker build` 与 CI build **同一 Dockerfile**。
- **一套 env 键**：`JWT_SECRET`、`DATABASE_URL`、`OPENAI_*`、`EMBEDDING_*`、`CORS_ORIGINS`、`NEXT_PUBLIC_API_URL` 等；**profile 只换值不换键**。
- **本地**：`compose --profile full` + `DEPLOY_PROFILE=local` + Ollama 冒烟。
- **晋级云**：推镜像 → 服务器/K8s 注入 **cloud profile** env → 同一拓扑（web/api/nginx 或 Ingress 等价）。
- CI：`deploy.yml` 构建镜像；可选 push GHCR。

**Non-Goals:**

- EP14 才做 Helm/TKE 编排细节
- Ollama 上云
- 自动购买腾讯云

## Decisions

### D0: 部署契约（核心）

```text
┌─────────────────────────────────────────────────────────┐
│  EP08 交付物（local 与 cloud 共用）                      │
│  · apps/web/Dockerfile  apps/api/Dockerfile             │
│  · infra/nginx/default.conf（Ingress 对照）             │
│  · .env.deployment.example（键 + local/cloud 取值说明） │
└─────────────────────────────────────────────────────────┘
         │ local                          │ cloud
         ▼                                ▼
  compose --profile full          push 镜像 + cloud env
  .env.deployment.local           VM compose 或 EP14 Helm
  Ollama qwen3:8b                 百炼 / 托管 PG·Redis
```

**原则**：本地不是「玩具栈」；是 **staging 仿真**。参数在 local 调对后，cloud **只改连接串与域名**，不 fork 镜像。

### D1: Compose profiles 保留 dev 默认

`postgres` + `redis` 无 profile；`api`、`web`、`nginx` 在 `profiles: [full]`。

### D2–D3: 镜像（已实现 Story 8.1）

Web standalone；API uvicorn；**tag 由 env 注入**：

```yaml
web:
  image: ${WEB_IMAGE:-memoryos-web:local}
api:
  image: ${API_IMAGE:-memoryos-api:local}
```

CI 构建 `memoryos-web:${GITHUB_SHA}`；云上 `export WEB_IMAGE=ghcr.io/.../web:sha`。

### D4: Nginx 拓扑

```text
Client → nginx
           ├─ /           → web:3000
           ├─ /api/chat*  → web:3000   (Next BFF，同源)
           └─ /api/v1/*   → api:8000   (SSE: buffering off)
```

云上：Ingress 复用相同 path 规则（EP14）。

### D5: 环境文件（替代 `.env.docker.full`）

| 文件 | 提交 | 用途 |
|:-----|:-----|:-----|
| `infra/docker/.env.deployment.example` | ✅ | **契约**：所有键 + `## LOCAL` / `## CLOUD` 注释示例 |
| `infra/docker/.env.deployment.local` | ❌ gitignore | 本地 full 实测（Ollama、compose 服务名） |
| `infra/docker/.env.deployment.cloud` | ❌ | 云 VM Compose 或导入 K8s Secret 前的草稿 |

`DEPLOY_PROFILE=local|cloud` 文档化；应用 **不强制**读此变量，仅给人/脚本区分。

**宿主机 `pnpm dev`**：继续 `apps/api/.env`、`apps/web/.env.local`（与部署 env **键对齐**，值用 localhost）。

### D6: Profile 取值对照（关键参数）

| 键 | LOCAL（compose full） | CLOUD |
|:---|:----------------------|:------|
| `DATABASE_URL` | `@postgres:5432` | 托管 PG 连接串 |
| `REDIS_URL` | `redis://redis:6379/0` | 云 Redis URL |
| `OPENAI_BASE_URL` | `http://host.docker.internal:11434/v1` | 百炼 compatible URL |
| `OPENAI_MODEL` | `qwen3:8b` | `qwen-turbo` 等 |
| `EMBEDDING_BASE_URL` | 同 Ollama | 百炼 embedding URL |
| `EMBEDDING_MODEL` | `mxbai-embed-large` | `text-embedding-v4` |
| `CORS_ORIGINS` | `http://localhost:8080` | `https://your.domain` |
| `NEXT_PUBLIC_API_URL` | build-arg：经 Nginx 的对外 URL | `https://your.domain` |
| `API_UPSTREAM_URL`（新增，task 3.x） | `http://api:8000`（BFF 服务端调 FastAPI） | 集群内 service URL |

### D7: 迁移

`docker compose --profile full run api alembic upgrade head`；cloud 同理（一次性 job 或文档步骤）。

### D8: Ollama（仅 local profile）

宿主机 Ollama；chat **`qwen3:8b`**；embed **`mxbai-embed-large`**（1024 维）。

### D9: LLM / Embedding 分离

`EMBEDDING_BASE_URL` 独立于 `OPENAI_BASE_URL`（task 6.1）。

### D10: CI

`.github/workflows/deploy.yml`：`docker build` web + api；`push` 仅当配置 `GHCR_TOKEN`（文档说明）。

### D11: 晋级路径（文档）

`deployment.md` §Local smoke → §Promote to cloud：

1. Local full 绿（SSE、RAG、登录）
2. CI 或本地 `docker build` 得相同 tag
3. `docker push` 到 registry
4. 云主机：pull 镜像 + `.env.deployment.cloud` + `compose --profile full up`
5. EP14：同一镜像写入 Helm values

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| local/cloud env 漂移 | 单文件 example 双 section；键名禁止分叉 |
| Web BFF 误用浏览器 URL 调 api | `API_UPSTREAM_URL` 服务端专用 |
| 换 embed 模型 | re-ingest 文档 |
| 本地无 registry | 默认 `image:local` tag；云再换 |

## Migration Plan

1. 完成 compose + deployment env + nginx（task 3–5）
2. Local profile 冒烟
3. CI build 镜像
4. 文档晋级 cloud；EP14 Helm 引用同一镜像名

## Open Questions

- [ ] `API_UPSTREAM_URL` 命名 — implement 时与 web BFF 对齐
- [ ] 云第一阶段：VM + Compose 还是直接 TKE — 文档两种都写，EP14 偏 K8s

## 与 EP14

| EP08 | EP14 |
|:-----|:-----|
| 镜像 Dockerfile、env 契约、CI build | Helm、TKE、Ingress TLS |
| VM Compose + cloud profile 可先行 | 消费 `WEB_IMAGE`/`API_IMAGE` |
