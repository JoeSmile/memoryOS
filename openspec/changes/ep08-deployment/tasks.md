## 0. Human review（apply 前必过）

> propose 完成后 **必须停在这里**等人审；未勾选前 **禁止**写业务代码。

- [x] **Tasks reviewed by human** — 人审通过后再 `/opsx:apply`、`/work-next` 或说「继续实现」

### Review checklist

- [x] Docker web + api 成对；full profile 含 nginx + pg + redis
- [x] 默认 `docker compose up` **仍仅** PG+Redis（Harness / `pnpm db:up` 不破）
- [x] Nginx SSE：`proxy_buffering off` 有 task + 文档
- [x] **部署契约**：`.env.deployment.example` 含 local/cloud **同一套键**、不同取值说明
- [x] **镜像可晋级**：`WEB_IMAGE`/`API_IMAGE` + CI build 与本地同 Dockerfile
- [x] **local profile** Ollama：`qwen3:8b` + embed；**cloud profile** 百炼注释（键不变）
- [x] `deployment.md` 含 local 冒烟 + cloud 晋级步骤
- [x] Harness / CI **仍 mock**（无 Key 路径不变）
- [x] 与 [`EP08-deployment.md`](../../docs/tasks/epics/EP08-deployment.md) Story 8.1–8.6 一致
- [x] EP07 已砍掉，本 change 无 workflow scope
- [x] 每条 task ≤3 文件 / ~150 行

**Reviewer notes:** 2026-06-15 修订 — 本地 Docker 为 staging 仿真，非死胡同；与 EP14 共用镜像/env 契约。

---

## 1. Web Dockerfile（Story 8.1）

- [x] 1.1 `next.config.ts` 启用 `output: "standalone"`
  - 预计文件：1 · 层：`apps/web/next.config.ts`

- [x] 1.2 `apps/web/Dockerfile` 多阶段 + `apps/web/.dockerignore` + 非 root
  - 预计文件：2 · 层：`Dockerfile` + `.dockerignore`

## 2. API Dockerfile（Story 8.1）

- [x] 2.1 `apps/api/Dockerfile` 多阶段 + `apps/api/.dockerignore` + 非 root uvicorn
  - 预计文件：2 · 层：`Dockerfile` + `.dockerignore`

## 3. Compose full + 部署 env（Story 8.2）

- [x] 3.1 `infra/docker/docker-compose.yml` — `profiles: [full]`；`WEB_IMAGE`/`API_IMAGE`；healthcheck；`extra_hosts`（Ollama）
  - 预计文件：1 · 层：`infra/docker/docker-compose.yml`

- [x] 3.2 `infra/docker/.env.deployment.example`（local/cloud 双 section）+ README 说明 `.env.deployment.local`
  - 预计文件：2 · 层：`.env.deployment.example` + `README.md`

## 4. Nginx（Story 8.3）

- [x] 4.1 `infra/nginx/default.conf` — `/` + `/api/chat` → web；`/api/v1/` → api；SSE buffering off
  - 预计文件：1 · 层：`infra/nginx/default.conf`

- [x] 4.2 compose 挂载 nginx；`infra/nginx/README.md`（含 Ingress 对照）
  - 预计文件：2 · 层：`docker-compose.yml` + `nginx/README.md`

## 5. 部署文档（Story 8.4）

- [x] 5.1 `docs/tech/deployment.md` — §Local smoke + §Promote to cloud（push 镜像、cloud env、migrate）
  - 预计文件：1 · 层：`docs/tech/deployment.md`

- [x] 5.2 更新 epic + [`L06`](../learning/L06-deployment.md) 部署契约与晋级路径
  - 预计文件：2 · 层：epic + L06

## 6. LLM Profile + Ollama local（Story 8.5）

- [x] 6.1 `Settings.embedding_api_base` + `EmbeddingService` + unit test
  - 预计文件：3 · 层：`config.py` + `embedding_service.py` + `tests/unit/test_embedding_service.py`

- [x] 6.2 `.env.deployment.example` + `apps/api/.env.example` — local（Ollama `qwen3:8b`）与 cloud（百炼）注释块；web `API_UPSTREAM_URL` 若需要
  - 预计文件：2–3 · 层：example 文件 + 可选 web env

- [ ] 6.3 `docs/tech/ollama-local.md`（**仅 local profile**）+ `deployment.md` 链接
  - 预计文件：2 · 层：`ollama-local.md` + `deployment.md`

- [ ] 6.4 `rag-embedding-chunking.md` §3.8 + L06 §5 更新
  - 预计文件：2 · 层：rag doc + L06

## 7. CI 镜像（Story 8.6）

- [ ] 7.1 `.github/workflows/deploy.yml` — PR/push `docker build` web+api（同 Dockerfile）；文档 optional push
  - 预计文件：1 · 层：`.github/workflows/deploy.yml`

## 8. Closeout

- [ ] 8.1 `compose --profile full config` + local 冒烟 + cloud 晋级 checklist；tasks 勾选
  - 预计文件：1 · 层：`tasks.md` + README
