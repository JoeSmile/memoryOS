# Ollama 本地 LLM（仅 local profile）

> **范围**：宿主机或 Docker Compose **local** 部署用 Ollama 作 Chat + Embedding。**Cloud profile** 使用百炼等托管 API，见 [`deployment.md` §4.2](./deployment.md#42-cloud-env) 与 [`infra/docker/.env.deployment.example`](../../infra/docker/.env.deployment.example) CLOUD 段。

相关文档：

- 全栈冒烟：[`deployment.md` §3](./deployment.md#3-local-smoke本地全栈验证)
- 宿主机 dev env：[`apps/api/.env.example`](../../apps/api/.env.example) Profile B
- Compose env：[`infra/docker/.env.deployment.example`](../../infra/docker/.env.deployment.example) LOCAL 段
- 学习路线：[`L06-deployment.md` §5](../tasks/learning/L06-deployment.md#5-ollama-本地-llm--embedding)

---

## 1. 为什么用 Ollama

| 场景 | 选择 |
|:-----|:-----|
| 本地验证部署、无 API Key | 宿主机 GPU/Metal 跑模型，Compose 内 API 经 `host.docker.internal` 访问 |
| CI / Harness | 不设 `OPENAI_API_KEY` → 确定性 mock（与 Ollama 无关） |
| 生产 / cloud | **不用 Ollama**；换百炼 Key + 同一套 env **键** |

Ollama **不在** `docker compose --profile full` 里起容器；只在 Mac/宿主机运行。

---

## 2. 安装与启动

1. 安装 [Ollama](https://ollama.com)（Mac 可用桌面应用，会自动 `serve`）。
2. 或终端：

```bash
ollama serve
```

3. 拉取推荐模型（与 pgvector `vector(1024)` 一致）：

```bash
ollama pull qwen3:8b
ollama pull mxbai-embed-large
```

4. 确认服务：

```bash
curl -s http://127.0.0.1:11434/api/tags
```

| 用途 | 模型 | 维度 | 说明 |
|:-----|:-----|:-----|:-----|
| Chat | `qwen3:8b` | — | 中文友好；首条回复冷启动可能 1–2 分钟 |
| Embedding | `mxbai-embed-large` | **1024** | 须与 `EMBEDDING_DIMENSIONS` / migration 一致 |

勿用 `nomic-embed-text`（768 维）等维度不匹配的模型，否则 ingest / 检索会报错。

---

## 3. OpenAI 兼容 API

Ollama 暴露 OpenAI 兼容端点（MemoryOS 通过 LangChain `ChatOpenAI` / `OpenAIEmbeddings` 调用）：

| 能力 | 路径 |
|:-----|:-----|
| Chat | `{base}/chat/completions` |
| Embedding | `{base}/embeddings` |

`base` 一般为 `http://127.0.0.1:11434/v1`（宿主机）或 `http://host.docker.internal:11434/v1`（Compose 内 api 容器）。

---

## 4. 环境变量（Chat 与 Embed 分离）

MemoryOS 将 **Chat LLM** 与 **Embedding** 分开配置 base URL（task 6.1：`EMBEDDING_BASE_URL` 未设时回退 `OPENAI_BASE_URL`）。

| 键 | 作用 |
|:---|:-----|
| `OPENAI_API_KEY` | 设为 `ollama` 启用 **live**（Ollama 不校验，但空 Key 会走 mock） |
| `OPENAI_BASE_URL` | Chat 的 OpenAI-compatible base |
| `OPENAI_MODEL` | Chat 模型名（如 `qwen3:8b`） |
| `EMBEDDING_BASE_URL` | Embedding base（可与 Chat 相同或不同 endpoint） |
| `EMBEDDING_MODEL` | Embedding 模型（如 `mxbai-embed-large`） |
| `EMBEDDING_DIMENSIONS` | `1024`（与 Alembic / `rag_constants` 一致） |

### 4.1 宿主机 dev（`pnpm dev:stack`）

使用 `apps/api/.env`（参考 Profile B）：

```env
OPENAI_API_KEY=ollama
OPENAI_MODEL=qwen3:8b
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
EMBEDDING_BASE_URL=http://127.0.0.1:11434/v1
EMBEDDING_MODEL=mxbai-embed-large
EMBEDDING_DIMENSIONS=1024
```

浏览器仍走 `apps/web/.env.local` → `NEXT_PUBLIC_API_URL=http://localhost:8000`。

### 4.2 Docker Compose full（local profile）

使用 **`infra/docker/.env.deployment.local`**（勿放在 `apps/api/`）：

```env
OPENAI_API_KEY=ollama
OPENAI_MODEL=qwen3:8b
OPENAI_BASE_URL=http://host.docker.internal:11434/v1
EMBEDDING_BASE_URL=http://host.docker.internal:11434/v1
EMBEDDING_MODEL=mxbai-embed-large
EMBEDDING_DIMENSIONS=1024
```

Compose 为 api 配置 `extra_hosts: host.docker.internal:host-gateway`（Linux 必需）。Web 镜像 build 时 `NEXT_PUBLIC_API_URL=http://localhost:8080`（Nginx 入口）。

Ollama 可在 Compose **之后** 再启动；聊天失败时 `docker compose ... restart api`。

---

## 5. 换模型与 re-ingest

| 变更 | 动作 |
|:-----|:-----|
| 只换 Chat 模型（维度不变） | 改 `OPENAI_MODEL`，重启 api |
| 换 Embedding 模型或 `EMBEDDING_DIMENSIONS` | 改 env + **全量 re-ingest** 知识库与长期记忆向量 |
| 从百炼切到 Ollama（或反向） | 换 env + re-ingest（旧向量与新区间不兼容） |

pgvector 列宽固定为 1024；维度不一致会在 insert / cosine search 时报错。

---

## 6. 验证

**宿主机：**

```bash
curl -s http://127.0.0.1:11434/api/tags
```

**Compose 内 api 容器：**

```bash
docker exec memoryos-api curl -s http://host.docker.internal:11434/api/tags
```

**应用层：**

- 登录后聊天 SSE 出现真实 token（非 mock 固定文案）
- （可选）ingest 小样后 RAG 检索有结果

---

## 7. 故障排查

| 现象 | 原因 | 处理 |
|:-----|:-----|:-----|
| 聊天仍是 mock 文案 | `OPENAI_API_KEY` 为空 | local 设为 `ollama` |
| api 容器连不上 Ollama | 用了 `127.0.0.1:11434` | Compose 内改 `host.docker.internal` |
| `502` / empty embedding | 未 `ollama pull` | pull 对应模型 |
| insert/search 维度错误 | 768 维 embed 模型 | 改用 `mxbai-embed-large` 或 re-migrate（不推荐） |
| RAG 结果乱 | 混用百炼与 Ollama 向量 | 换 backend 后全量 re-ingest |
| 首条回复很慢 | 模型冷加载 | 正常；可预热或换更小模型 |

更多 Compose / Nginx 问题见 [`deployment.md` §6](./deployment.md#6-故障排查)。
