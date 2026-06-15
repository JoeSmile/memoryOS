## 0. Human review（apply 前必过）

> propose 完成后 **必须停在这里**等人审；未勾选前 **禁止**写业务代码。

- [ ] **Tasks reviewed by human** — 人审通过后再 `/opsx:apply`、`/work-next` 或说「继续实现」

### Review checklist

- [x] Docker web + api 成对；full profile 含 nginx + pg + redis
- [x] 默认 `docker compose up` **仍仅** PG+Redis（Harness / `pnpm db:up` 不破）
- [x] Nginx SSE：`proxy_buffering off` 有 task + 文档
- [x] `.env.docker.full.example` 无真实密钥
- [x] **仅本地 Docker**，无上云 / SSL / deploy CI scope
- [x] **Ollama**：LLM + Embedding **分离** base URL/model；Docker API → `host.docker.internal:11434`
- [x] **Embedding 维度**与 `EMBEDDING_DIMENSIONS`（1024）一致；换模型需 re-ingest 已文档化
- [x] Harness / CI **仍 mock**（无 Key 路径不变）
- [x] 与 [`EP08-deployment.md`](../../docs/tasks/epics/EP08-deployment.md) Story 8.1–8.5 一致
- [x] EP07 已砍掉，本 change 无 workflow scope
- [x] 每条 task ≤3 文件 / ~150 行

**Reviewer notes:**（可选）

---

## 1. Web Dockerfile（Story 8.1）

- [ ] 1.1 `next.config.ts` 启用 `output: "standalone"`
  - 预计文件：1 · 层：`apps/web/next.config.ts`

- [ ] 1.2 `apps/web/Dockerfile` 多阶段 + `apps/web/.dockerignore` + 非 root
  - 预计文件：2 · 层：`Dockerfile` + `.dockerignore`

## 2. API Dockerfile（Story 8.1）

- [ ] 2.1 `apps/api/Dockerfile` 多阶段 + `apps/api/.dockerignore` + 非 root uvicorn
  - 预计文件：2 · 层：`Dockerfile` + `.dockerignore`

## 3. Compose full profile（Story 8.2）

- [ ] 3.1 `infra/docker/docker-compose.yml` — `profiles: [full]` 增加 api、web、nginx；healthcheck、`depends_on`；api `extra_hosts` 供 Ollama
  - 预计文件：1 · 层：`infra/docker/docker-compose.yml`

- [ ] 3.2 `infra/docker/.env.docker.full.example` + 更新 `infra/docker/README.md`
  - 预计文件：2 · 层：`.env.docker.full.example` + `README.md`

## 4. Nginx（Story 8.3）

- [ ] 4.1 `infra/nginx/default.conf` — `/` → web、`/api/` → api、SSE location（buffering off、长超时）；本地 HTTP
  - 预计文件：1 · 层：`infra/nginx/default.conf`

- [ ] 4.2 compose 挂载 nginx 配置；`infra/nginx/README.md` SSE 说明
  - 预计文件：2 · 层：`docker-compose.yml`（nginx volumes）+ `nginx/README.md`

## 5. 本地文档与冒烟（Story 8.4）

- [ ] 5.1 `docs/tech/deployment.md` — 本地 full 启动、端口、Alembic migrate、SSE 冒烟（**无上云**）
  - 预计文件：1 · 层：`docs/tech/deployment.md`

- [ ] 5.2 更新 [`EP08-deployment.md`](../../docs/tasks/epics/EP08-deployment.md) 链到 deployment.md；[`L06`](../learning/L06-deployment.md) 勾选/链接
  - 预计文件：2 · 层：epic + L06

## 6. Ollama 接入（Story 8.5）

- [ ] 6.1 `Settings` 增加 `embedding_api_base`（与 chat `OPENAI_BASE_URL` 分离）；`EmbeddingService` 使用独立 base；unit test
  - 预计文件：3 · 层：`config.py` + `embedding_service.py` + `tests/unit/test_embedding_service.py`

- [ ] 6.2 `apps/api/.env.example` + `.env.docker.full.example` — Ollama 预设（`OPENAI_*` chat + `EMBEDDING_*` + `host.docker.internal`）
  - 预计文件：2 · 层：`.env.example` + `.env.docker.full.example`

- [ ] 6.3 `docs/tech/ollama-local.md` — 安装、`ollama pull`、推荐模型对、维度/re-ingest、Docker 联网；`deployment.md` 链到 Ollama 冒烟
  - 预计文件：2 · 层：`ollama-local.md` + `deployment.md`（链接段）

- [ ] 6.4 更新 [`rag-embedding-chunking.md`](../../docs/tech/rag-embedding-chunking.md) §3.8 — EP08 落地 Ollama 可选后端；L06 §5 Ollama 学习勾选
  - 预计文件：2 · 层：`rag-embedding-chunking.md` + `L06-deployment.md`

## 7. Closeout

- [ ] 7.1 本地验证：`docker compose --profile full config` + Ollama 冒烟步骤；`tasks.md` 勾选
  - 预计文件：1 · 层：`openspec/changes/ep08-deployment/tasks.md` 勾选 + README 一句
