## Context

- **现状**：`infra/docker/docker-compose.yml` 仅 **postgres + redis**（EP03）；应用在宿主机 `pnpm dev:web` / `scripts/api.sh dev`；CI 仅有 `api-harness.yml`。
- **约束**：EP08 = **本地单机 Compose + Nginx** 跑通全栈；SSE chat 必须可用；与 Harness 兼容（CI 仍可只起 PG+Redis 跑测试）。
- **依赖**：EP03 schema、EP02 SSE、EP08 前功能已合并 main。

## Goals / Non-Goals

**Goals:**

- `docker compose --profile full up` 本地验证全栈。
- Nginx 正确转发 `/api` SSE（`proxy_buffering off`）。
- 文档化本地 full 启动、migrate、SSE 冒烟与 `.env.docker.full.example`。
- **Ollama**：宿主机推理；API 经 OpenAI 兼容端点分别配置 chat LLM 与 embedding；full stack 可真实对话 + RAG（非 mock）。

**Non-Goals:**

- 腾讯云、域名、SSL、安全组、生产 CI/CD
- Ollama **容器化进 Compose**（GPU/Metal 复杂；EP08 用宿主机 Ollama）
- K8s / Helm / TKE（→ EP14）
- 多环境 Terraform、自动 SSL
- 生产 Remote Graph / 多 API 副本

## Decisions

### D1: Compose profiles 保留 dev 默认

**选择**：现有 `postgres` + `redis` 服务 **无 profile**（默认 `docker compose up` = 今日行为）；`api`、`web`、`nginx` 加 `profiles: [full]`。  
**理由**：不破坏 `pnpm db:up`、Harness、开发者习惯。

### D2: Next.js standalone 镜像

**选择**：`next.config.ts` 增加 `output: "standalone"`；Dockerfile 多阶段：deps → build → `node:20-alpine` runtime，拷贝 `.next/standalone` + `static` + `public`。  
**理由**：L06 与 Next 官方 Docker 推荐；缩小镜像。

### D3: API 镜像

**选择**：Python 3.12 slim 多阶段；`requirements.txt` install；非 root `appuser`；`CMD uvicorn app.main:app --host 0.0.0.0 --port 8000`。  
**Compose 内**：`DATABASE_URL=postgresql+asyncpg://...@postgres:5432/...`，`REDIS_URL=redis://redis:6379/0`。

### D4: Nginx 拓扑（本地 HTTP）

```text
Browser → nginx:8080 (或 80)
            ├─ /        → web:3000
            └─ /api/v1/ → api:8000  (SSE: buffering off, read_timeout 3600s)
```

Web 容器 env：优先 **同源 Nginx 反代**（`NEXT_PUBLIC_*` 空或相对路径）— implement 时读 `api-client.ts` 定案。

### D5: 环境文件

- 开发：继续 `apps/api/.env`
- Compose full 模板：`infra/docker/.env.docker.full.example`（`JWT_SECRET`、`OPENAI_API_KEY` 等占位，无真实密钥）
- Compose full：`env_file: .env.docker.full`（gitignore 真实 `.env.docker.full`）

### D6: 迁移

**选择**：documented `docker compose --profile full run api alembic upgrade head`；首版 **文档 manual step**，避免 silently fail migrate。

### D7: 文档

`docs/tech/deployment.md`：仅 **本地** full stack 启动、端口、migrate、SSE curl/浏览器验证；**不含** 上云步骤。

### D8: Ollama 拓扑（宿主机）

**选择**：Ollama 跑在 **宿主机**（`ollama serve`，默认 `:11434`），**不**纳入 Compose full profile。  
**API 容器**经 `http://host.docker.internal:11434/v1` 访问（compose `extra_hosts: host.docker.internal:host-gateway`）。  
**宿主机 dev** 用 `http://127.0.0.1:11434/v1`。

**理由**：Mac Metal / 本机 GPU 访问简单；避免 Ollama 镜像体积与 GPU passthrough。

### D9: LLM 与 Embedding 分离配置

**选择**：

| 用途 |  env | 示例（Ollama） |
|:-----|:-----|:---------------|
| Chat LLM | `OPENAI_API_KEY`（占位 `ollama`）、`OPENAI_BASE_URL`、`OPENAI_MODEL` | `qwen2.5:7b` |
| Embedding | 新增 `EMBEDDING_BASE_URL`（fallback 到 chat base）、`EMBEDDING_MODEL`、`EMBEDDING_DIMENSIONS` | `mxbai-embed-large`（**1024** 维，与 pgvector 一致） |

**Mock 门控**：仍仅看 `OPENAI_API_KEY` 是否为空（Harness/CI 不设 Key → mock）；Ollama 本地设 `OPENAI_API_KEY=ollama` 启用 live。

**换 embed 模型/维度**：须 re-ingest；文档写清（见 `ollama-local.md`）。

### D10: 推荐模型与冒烟

- `ollama pull qwen2.5:7b`（或文档列出的等价 chat 模型）
- `ollama pull mxbai-embed-large`（1024 维）
- 冒烟：full stack up → ingest 小样 → chat SSE 经 Nginx 有真实 token；RAG 检索非 mock 向量

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| Next standalone 漏 static | Dockerfile checklist + 本地 full profile 冒烟 |
| SSE 被 Nginx 缓冲 | 独立 location + 测试 doc |
| 镜像 build 慢 | layer cache、dockerignore |
| 本地端口与 dev 冲突 | compose 映射文档化（如 nginx 8080） |
| Ollama 未启动 / Docker 连不上 host | health 文档 + `curl host.docker.internal:11434` 排查 |
| Embed 维度与 pgvector 不一致 | 默认 `mxbai-embed-large` + 1024；换模型必 re-ingest |

## Migration Plan

1. 合并 Dockerfile + compose profile
2. 本地 `compose --profile full up` + 宿主机 Ollama 冒烟 chat SSE / RAG
3. EP14 再基于同一镜像上 K8s / 云

## Open Questions

- [ ] Web 调 API 基址：同源 Nginx 反代 vs `NEXT_PUBLIC_*` — implement 时读 `api-client.ts` 定案
- [ ] Ollama chat 默认模型：`qwen2.5:7b` vs `llama3.2` — 文档定推荐，implement 不硬编码

## 与 EP13/EP14

| EP08 | 后续 |
|:-----|:-----|
| 本地 Compose + Nginx 验证 | EP13 distributed profile |
| 镜像与 compose 文档 | EP14 K8s + 腾讯云 TKE + CI 上云 |

见 [post-mvp-roadmap.md](../../docs/tasks/post-mvp-roadmap.md)。
