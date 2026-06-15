# MemoryOS 部署指南（EP08）

> **部署契约**：同一套 **Dockerfile**、同一套 **env 键**（`.env.deployment.example`），本地 `local` profile 验证通过后，换 `cloud` profile + registry tag 上云。EP14 只做 K8s/Helm，不重做镜像。

相关文档：

- Compose 与 env 模板：[`infra/docker/README.md`](../../infra/docker/README.md)
- Nginx / Ingress 对照：[`infra/nginx/README.md`](../../infra/nginx/README.md)
- Ollama（仅 local）：本文 §3.2；详文档见 Story 8.5 / `ollama-local.md`（待 task 6.3）
- 学习路线：[`L06-deployment.md`](../tasks/learning/L06-deployment.md)

---

## 1. 架构概览

```text
浏览器 → nginx:8080
           ├─ /              → web:3000   (Next.js)
           ├─ /api/chat*     → web:3000   (BFF SSE)
           └─ /api/v1/*      → api:8000   (FastAPI SSE)

api ──→ postgres / redis（Compose 网络）
api ──→ host.docker.internal:11434（宿主机 Ollama，仅 local profile）
```

| 组件 | 镜像 | 说明 |
|:-----|:-----|:-----|
| web | `memoryos-web:<tag>` | Next standalone + BFF |
| api | `memoryos-api:<tag>` | FastAPI + Alembic |
| nginx | `nginx:1.27-alpine` | 官方镜像 + `default.conf` |
| postgres / redis | 官方镜像 | 默认 `docker compose up` 也会启动 |

**Ollama 不在 Compose 内** — 在 Mac/宿主机运行，API 通过 `host.docker.internal` 访问。

---

## 2. 前置条件

- Docker Desktop / Engine + Compose v2
- 能拉取或已缓存 `node:20-alpine`、`python:3.12-slim`（拉取失败见 §6.1）
- 仓库根目录可 `pnpm install`（构建 web 镜像时）
- **local LLM**：宿主机 [Ollama](https://ollama.com) + `qwen3:8b`、`mxbai-embed-large`

---

## 3. Local smoke（本地全栈验证）

### 3.1 准备部署 env

```bash
cd infra/docker
cp .env.deployment.example .env.deployment.local
```

编辑 `.env.deployment.local`（**勿提交 git**）：

| 键 | local 典型值 |
|:---|:-------------|
| `JWT_SECRET` | 长随机串（≥32 字符） |
| `OPENAI_API_KEY` | `ollama`（占位，启用 live） |
| `OPENAI_BASE_URL` | `http://host.docker.internal:11434/v1` |
| `OPENAI_MODEL` | `qwen3:8b` |
| `EMBEDDING_MODEL` | `mxbai-embed-large` |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8080` |
| `API_UPSTREAM_URL` | `http://api:8000` |

> env 文件路径必须是 **`infra/docker/.env.deployment.local`**，不是 `apps/api/`。

### 3.2 启动 Ollama（宿主机）

```bash
# Mac：打开 Ollama 应用，或
ollama serve

ollama pull qwen3:8b
ollama pull mxbai-embed-large
curl -s http://127.0.0.1:11434/api/tags
```

Ollama 可在 Compose **之后** 再启动，一般 **无需** 重建容器；聊天失败时 `docker compose ... restart api`。

### 3.3 构建镜像

```bash
# 仓库根目录
docker build -f apps/web/Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8080 \
  -t memoryos-web:local .

docker build -f apps/api/Dockerfile -t memoryos-api:local apps/api
```

`NEXT_PUBLIC_*` 在 **build 时** 写入客户端包；改入口 URL 须 **rebuild web**。

### 3.4 启动全栈

```bash
cd infra/docker
docker compose --env-file .env.deployment.local --profile full up -d
docker compose --profile full ps
```

期望 5 个容器 healthy：`nginx`、`web`、`api`、`postgres`、`redis`。

入口：**http://localhost:8080**（`NGINX_HTTP_PORT` 可改）。

### 3.5 数据库迁移

```bash
docker compose --env-file .env.deployment.local --profile full run --rm api alembic upgrade head
```

### 3.6 冒烟清单

- [ ] `curl -sS http://localhost:8080/` 返回 HTML
- [ ] 注册 / 登录成功
- [ ] 聊天 SSE 有真实 token（非 mock 占位文案）
- [ ] 首条 Ollama 回复可能 **1–2 分钟**（冷启动加载模型）
- [ ] （可选）RAG：需已 ingest；换 embed 模型后须 re-ingest

### 3.7 停止

```bash
cd infra/docker
docker compose --profile full down          # 保留数据卷
docker compose --profile full down -v       # 清空 PG/Redis 数据（慎用）
```

仅停 PG+Redis（宿主机 dev）：`pnpm db:down` 或 `docker compose down`（不带 profile）。

---

## 4. Promote to cloud（晋级上云）

原则：**不换 Dockerfile**，只换 **镜像 tag** 与 **env 值**。

### 4.1 构建并推送（示例 GHCR）

```bash
export TAG=$(git rev-parse --short HEAD)
export REGISTRY=ghcr.io/<org>/memoryos

docker build -f apps/web/Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL=https://your.domain \
  -t $REGISTRY/web:$TAG .

docker build -f apps/api/Dockerfile -t $REGISTRY/api:$TAG apps/api

docker push $REGISTRY/web:$TAG
docker push $REGISTRY/api:$TAG
```

CI 自动化见 task 7.1（`deploy.yml`）。

### 4.2 Cloud env

```bash
cd infra/docker
cp .env.deployment.example .env.deployment.cloud
```

按 example 中 **CLOUD** 注释修改（键名不变）：

| 键 | cloud 典型值 |
|:---|:-------------|
| `WEB_IMAGE` / `API_IMAGE` | `$REGISTRY/web:$TAG` |
| `DATABASE_URL` | 托管 PostgreSQL 连接串 |
| `REDIS_URL` | 云 Redis URL |
| `OPENAI_*` | 百炼 Key + compatible URL |
| `CORS_ORIGINS` / `NEXT_PUBLIC_API_URL` | `https://your.domain` |
| `API_UPSTREAM_URL` | `http://api:8000`（Compose）或 K8s Service DNS |

**不要** 在 cloud 使用 Ollama / `host.docker.internal`。

### 4.3 云主机 Compose（与 local 同一文件）

```bash
docker compose --env-file .env.deployment.cloud --profile full pull
docker compose --env-file .env.deployment.cloud --profile full up -d
docker compose --env-file .env.deployment.cloud --profile full run --rm api alembic upgrade head
```

### 4.4 与 EP14（K8s）衔接

- Helm values 引用同一 `WEB_IMAGE` / `API_IMAGE`
- Secret/ConfigMap 键与 `.env.deployment.example` 对齐
- Ingress path 规则对照 [`infra/nginx/default.conf`](../../infra/nginx/default.conf)

---

## 5. 环境对照速查

| 场景 | API / DB env | Web |
|:-----|:-------------|:----|
| `pnpm dev:stack` | `apps/api/.env`（`localhost`） | `apps/web/.env.local` |
| Compose full local | `infra/docker/.env.deployment.local` | 镜像 build-arg + `API_UPSTREAM_URL` |
| Cloud | `.env.deployment.cloud` 或 K8s Secret | rebuild with 公网 URL |

---

## 6. 故障排查

### 6.1 `docker build` 拉镜像超时

`auth.docker.io` / `DeadlineExceeded` → 配置 Docker **registry-mirrors** 或代理，先 `docker pull node:20-alpine` 成功再 build。

### 6.2 Compose 里看不到 Ollama 容器

**正常**。Ollama 在宿主机；确认 `curl http://127.0.0.1:11434/api/tags`。

### 6.3 API 容器访问 Ollama

```bash
docker exec memoryos-api curl -s http://host.docker.internal:11434/api/tags
```

失败：检查 Ollama 是否运行、`.env.deployment.local` 中 `OPENAI_BASE_URL`。

### 6.4 聊天 mock 或 502

- `OPENAI_API_KEY` 为空 → mock；local 应设为 `ollama`
- BFF 应用 `API_UPSTREAM_URL=http://api:8000`，勿用 `localhost:8080`
- 查看 `docker logs memoryos-api`、`docker logs memoryos-web`

### 6.5 改 env 后何时重启

| 变更 | 动作 |
|:-----|:-----|
| 仅后开 Ollama | 通常不用重启 |
| 改 `.env.deployment.local` | `docker compose ... up -d api` 或 `restart api` |
| 改 `NEXT_PUBLIC_API_URL` | rebuild web 镜像 + recreate web |

---

## 7. 与开发路径关系

| 命令 | 作用 |
|:-----|:-----|
| `pnpm db:up` | 仅 PG+Redis（Harness / 宿主机 dev） |
| `pnpm dev:stack` | PG+Redis + 宿主机 web/api |
| `compose --profile full` | 容器化全栈 + Nginx（部署验证） |

三者可并存；全栈占用 **8080**（nginx），dev web 默认 **3000**、api **8000**。
