# EP08 — 本地 Docker 全栈

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 8 周 |
| **优先级** | P0 |
| **学习路线** | [L06-deployment.md](../learning/L06-deployment.md) |
| **OpenSpec** | [ep08-deployment](../../openspec/changes/ep08-deployment/design.md) |
| **MVP 后** | 上云 / K8s 见 [post-mvp-roadmap.md](../post-mvp-roadmap.md) · EP13 · EP14 |

> **范围**：**本地** Docker Compose 全栈（web + api + postgres + redis + nginx）跑通与冒烟；SSE 经 Nginx 可用；**本地 Ollama** 接入 LLM + Embedding（无外网 Key 也可演示）。**不上云**——腾讯云 / SSL / 生产 CI 留 **EP14（K8s）**。

---

## Story 8.1 Docker

- [ ] `apps/web`、`apps/api` 多阶段 Dockerfile
- [ ] `.dockerignore`、非 root 用户

## Story 8.2 Docker Compose

- [ ] 本地一键：`docker compose --profile full up`
- [ ] web、api、postgres、redis、nginx
- [ ] `.env.docker.full.example`（Compose full 用，无真实密钥）

## Story 8.3 Nginx（本地）

- [ ] SSE：`proxy_buffering off`、长超时
- [ ] `/` → web、`/api/` → api（HTTP 即可）
- [ ] 静态资源、CORS（若需要）

## Story 8.4 本地文档与冒烟

- [ ] `docs/tech/deployment.md` — full profile 启动、Alembic migrate、SSE 验证步骤
- [ ] `infra/docker/README.md` 与 epic / L06 链接同步

## Story 8.5 本地 Ollama（LLM + Embedding）

- [ ] 宿主机安装 Ollama；`ollama pull` 推荐 chat + embed 模型
- [ ] API：**LLM 与 Embedding 分离 base URL / model**（OpenAI 兼容）；Docker 内通过 `host.docker.internal:11434` 访问宿主机 Ollama
- [ ] `.env.example` / `.env.docker.full.example` 提供 Ollama 预设块
- [ ] `docs/tech/ollama-local.md` — 安装、模型、维度与 re-ingest、full stack 冒烟
- [ ] Harness / CI **仍 mock**（不设 Key 即可，行为不变）

---

## 移出 EP08（→ EP14 / 后续）

| 原 Story | 去向 |
|:---------|:-----|
| 腾讯云 / 安全组 | EP14 |
| 域名 / SSL / HTTPS | EP14 |
| dev/staging/prod 环境隔离 | EP14 |
| GitHub Actions 镜像 build / deploy | EP14 |

---

## 同步学习

- [ ] Docker 多阶段与网络（理解 / 落地）
- [ ] Nginx SSE 避坑（理解 / 落地）
- [ ] Compose profiles 与 dev 默认路径共存（理解 / 落地）
- [ ] Ollama 本地推理、OpenAI 兼容 API、LLM/Embed 分离配置（理解 / 落地）
