# EP08 — 部署契约与本地验证

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 8 周 |
| **优先级** | P0 |
| **学习路线** | [L06-deployment.md](../learning/L06-deployment.md) |
| **部署指南** | [deployment.md](../../tech/deployment.md) |
| **OpenSpec** | [ep08-deployment](../../openspec/changes/ep08-deployment/design.md) |
| **MVP 后** | K8s 编排见 [EP14](./EP14-k8s-cloud.md) · [post-mvp-roadmap.md](../post-mvp-roadmap.md) |

> **范围**：建立 **local → cloud 共用** 的部署契约（镜像 + env 键 + Nginx 规则）。本地 `compose --profile full` 用于 **验证流程与参数**；通过后 **同一镜像** push registry，换 **cloud profile** 上云。EP14 只做 K8s/Helm，**不重做 Dockerfile**。

---

## Story 8.1 Docker（✅ 完成）

- [x] `apps/web`、`apps/api` 多阶段 Dockerfile
- [x] `.dockerignore`、非 root 用户

## Story 8.2 Compose + 部署 env（✅ 完成）

- [x] `docker compose --profile full`；`WEB_IMAGE` / `API_IMAGE` 可配置
- [x] `.env.deployment.example`（**local / cloud 双 profile 注释**）
- [x] 本地实测：`.env.deployment.local`（gitignore）— 步骤见 [deployment.md §3](../../tech/deployment.md#3-local-smoke本地全栈验证)

## Story 8.3 Nginx（✅ 完成）

- [x] SSE：`proxy_buffering off`；BFF `/api/chat` 与 `/api/v1` 分流
- [x] 与云上 Ingress 规则对照文档 — [`infra/nginx/README.md`](../../../infra/nginx/README.md)

## Story 8.4 部署文档（local 验证 + cloud 晋级）（✅ 完成）

- [x] [`docs/tech/deployment.md`](../../tech/deployment.md) — 本地冒烟清单 + 推镜像上云步骤（§3 Local smoke · §4 Promote to cloud）

## Story 8.5 LLM Profile

- [ ] **local**：Ollama `qwen3:8b` + `mxbai-embed-large`；`EMBEDDING_BASE_URL` 分离
- [ ] **cloud**：同一 env 键，换百炼/托管 URL（example 中注释）
- [ ] `docs/tech/ollama-local.md`（仅 local profile）

## Story 8.6 CI 镜像流水线

- [ ] `deploy.yml`：`docker build` web + api（与本地同 Dockerfile）
- [ ] 可选 push GHCR；文档写 cloud 如何 `pull` 同一 tag

---

## 不在 EP08 实现（→ EP14）

| 项 | 说明 |
|:---|:-----|
| Helm / TKE 编排 | 消费 EP08 镜像与 env 键 |
| 自动 Terraform | 文档手动步骤即可 |
| Ollama 上云 | cloud profile 用 API Key |

---

## 同步学习

- [x] 部署契约：一套镜像、一套 env 键、profile 换值 — [L06 §0](../learning/L06-deployment.md#0-部署契约先建立心智模型) · [deployment.md §1–§5](../../tech/deployment.md)
- [x] Docker Compose full + Nginx SSE
- [ ] local Ollama vs cloud 百炼选型（代码分离见 Story 8.5）
- [ ] CI build 与云上 pull 同一 tag
