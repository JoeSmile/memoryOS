# L06 — 部署契约与本地验证（第 8 周）

**对应史诗**：EP08

---

## 0. 部署契约（先建立心智模型）

### 学什么

- [ ] 📖 **一套镜像**：`apps/web/Dockerfile`、`apps/api/Dockerfile` — 本地 build = CI build = 云上 pull
- [ ] 📖 **一套 env 键**：`.env.deployment.example` — `local` / `cloud` **只换值不换键**
- [ ] 📖 **本地** = staging 仿真：`compose --profile full` + `.env.deployment.local`
- [ ] 📖 **晋级云**：push 镜像 → cloud env → 同一 compose 或 EP14 Helm
- [ ] 🔧 `infra/docker/.env.deployment.example`、`docs/tech/deployment.md`

### 面试常问

- 如何避免「本地一套、生产重做」？镜像与配置如何分离？

---

## 1. Docker 多阶段构建

### 学什么

- [ ] 📖 阶段：deps install → build → runtime（alpine/slim）
- [ ] 📖 Next `output: "standalone"` 拷贝 static/public
- [ ] 📖 非 root 用户、`.dockerignore`、层缓存（先 COPY package.json）
- [ ] 🔧 `apps/web/Dockerfile`、`apps/api/Dockerfile`

### 面试常问

- 如何缩小 Node 镜像？standalone 解决什么问题？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 未拷 `.next/static` | 页面无样式 | Dockerfile 三步拷贝 |
| 构建上下文过大 | 慢 | dockerignore node_modules |
| arm vs amd 镜像 | 换机器跑不起来 | 本地先验证，上云见 EP14 |

---

## 2. Docker Compose 全栈

### 学什么

- [ ] 📖 服务：web、api、postgres、redis、nginx
- [ ] 📖 网络：服务名 DNS、`depends_on` + healthcheck
- [ ] 📖 卷：pg 数据持久化
- [ ] 📖 profiles：默认仅 PG+Redis；`--profile full` 起应用栈
- [ ] 🔧 `infra/docker/docker-compose.yml` 一键 `up`

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| api 用 localhost 连 db | 容器内连不上 | host=postgres |
| 无 healthcheck 就启动 web | 502 | 等 pg ready |
| .env 提交进镜像 | 密钥泄露 | runtime env 注入 |

---

## 3. Nginx 反向代理（本地）

### 学什么

- [ ] 📖 `proxy_pass` upstream；`client_max_body_size` 上传
- [ ] 📖 SSE：`proxy_buffering off`、`proxy_cache off`、读超时 ↑
- [ ] 🔧 `infra/nginx/default.conf`

### 面试常问

- 为什么 SSE 在 Nginx 后容易「不流式」？怎么配？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 默认 buffering | 一次性吐完 | off buffering |
| HTTP/2 某些组合问题 | 连接断 | 查官方建议，必要时 HTTP/1.1 到 upstream |
| CORS 双头 | 浏览器拦 | 只在一处设 CORS |

---

## 4. 本地冒烟与 cloud 晋级

### 学什么

- [ ] 📖 Local：`docker compose --profile full`、migrate、SSE 冒烟
- [ ] 📖 Cloud：`docker push`、`.env.deployment.cloud`、托管 PG/Redis、换 LLM 为百炼
- [ ] 🔧 `docs/tech/deployment.md` §Promote to cloud

---

## 5. Ollama 本地 LLM + Embedding

### 学什么

- [ ] 📖 [Ollama](https://ollama.com) 安装、`ollama serve`、`ollama pull`
- [ ] 📖 OpenAI 兼容 API（`/v1/chat/completions`、`/v1/embeddings`）
- [ ] 📖 **Chat 与 Embed 分离**：`OPENAI_BASE_URL` + `OPENAI_MODEL` vs `EMBEDDING_BASE_URL` + `EMBEDDING_MODEL`
- [ ] 📖 Docker 容器访问宿主机 Ollama：`host.docker.internal:11434`（Linux 需 `extra_hosts`）
- [ ] 📖 Embedding 维度须与 `EMBEDDING_DIMENSIONS`（1024）一致；换模型 → re-ingest
- [ ] 🔧 `docs/tech/ollama-local.md` · `.env.deployment.example` **local** 段

### 推荐模型对（local profile）

| 用途 | 模型 | 说明 |
|:-----|:-----|:-----|
| Chat | `qwen3:8b` | 中文友好；本机 Ollama |
| Embedding | `mxbai-embed-large` | **1024** 维，与 pgvector migration 一致 |

**cloud profile**：同一 env 键，`OPENAI_MODEL=qwen-turbo` 等，见 deployment example 注释。

`OPENAI_API_KEY=ollama` 为占位符（Ollama 不校验，但 MemoryOS 用它区分 mock/live）。

### 面试常问

- 为什么 LLM 和 Embedding 要分开配 base URL？  
- 换 embedding 模型为什么要 re-ingest？pgvector 维度不一致会怎样？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 容器内 `127.0.0.1:11434` | 连不上 Ollama | 用 `host.docker.internal` |
| `nomic-embed-text`（768 维） | insert/search 报错 | 用 1024 维模型或改 migration（EP08 不推荐） |
| 未 pull 模型 | 502 / empty response | 先 `ollama pull` |
| 与 DashScope 混用旧向量 | 召回乱 | 换 backend 后全量 re-ingest |

---

## 阶段自测

- [ ] 新人 30 分钟 Compose 起全栈  
- [ ] curl SSE 经 Nginx 仍流式  
- [ ] 说清 standalone 目录结构与启动命令
- [ ] 说清 local vs cloud profile 哪些键要改、哪些不用改
- [ ] 说清同一镜像如何从本地 push 到云

---

## 6. CI 镜像（Story 8.6）

- [ ] 📖 `deploy.yml` build 与本地同 Dockerfile
- [ ] 📖 EP14 只换 orchestrator，不换镜像

---

## MVP 后

- [ ] 📖 Helm / TKE 编排 → [EP14](../epics/EP14-k8s-cloud.md)（消费 EP08 镜像）
- [ ] 📖 分布式 profile → [L09](./L09-distributed-orchestration.md)
