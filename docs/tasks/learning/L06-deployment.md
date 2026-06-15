# L06 — 本地 Docker 全栈（第 8 周）

**对应史诗**：EP08

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

## 4. 本地冒烟与文档

### 学什么

- [ ] 📖 `docker compose --profile full` 启动顺序
- [ ] 📖 容器内 Alembic migrate
- [ ] 📖 curl / 浏览器验证 SSE 经 Nginx 仍流式
- [ ] 🔧 `docs/tech/deployment.md`

---

## 5. Ollama 本地 LLM + Embedding

### 学什么

- [ ] 📖 [Ollama](https://ollama.com) 安装、`ollama serve`、`ollama pull`
- [ ] 📖 OpenAI 兼容 API（`/v1/chat/completions`、`/v1/embeddings`）
- [ ] 📖 **Chat 与 Embed 分离**：`OPENAI_BASE_URL` + `OPENAI_MODEL` vs `EMBEDDING_BASE_URL` + `EMBEDDING_MODEL`
- [ ] 📖 Docker 容器访问宿主机 Ollama：`host.docker.internal:11434`（Linux 需 `extra_hosts`）
- [ ] 📖 Embedding 维度须与 `EMBEDDING_DIMENSIONS`（1024）一致；换模型 → re-ingest
- [ ] 🔧 `docs/tech/ollama-local.md` · `.env.docker.full.example` Ollama 块

### 推荐模型对（EP08 默认文档）

| 用途 | 模型 | 说明 |
|:-----|:-----|:-----|
| Chat | `qwen2.5:7b` | 中文友好；RAM ~8GB 量级 |
| Embedding | `mxbai-embed-large` | **1024** 维，与 pgvector migration 一致 |

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
- [ ] 宿主机 Ollama + full stack：真实 chat token + RAG 检索（非 mock）

---

## MVP 后（不占 EP08 范围）

- [ ] 📖 腾讯云、域名、SSL、GitHub Actions 镜像 CI → [EP14](../epics/EP14-k8s-cloud.md)
- [ ] 📖 分布式 Compose profile、Remote Graph → [L09](./L09-distributed-orchestration.md)
- [ ] 📖 EP08 本地 Compose 与 EP14 K8s 如何选型 → [post-mvp-roadmap.md](../post-mvp-roadmap.md)
