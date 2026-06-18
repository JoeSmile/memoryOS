# MemoryOS 代码地图（Code Map）

> **用途**：Agent / 新同学 **5 分钟建立 mental model**；改功能前先查「入口 → 编排 → 落点」。  
> **维护**：跨层大改（Chat SSE、RAG、Agent、Memory）后更新对应 §；细则仍以 BE/FE engineering 为准。

**关联**：[BE-engineering.md](./BE-engineering.md) · [FE-engineering.md](./FE-engineering.md) · [chat-rag-stream.md](./chat-rag-stream.md) · [langgraph-chat.md](./langgraph-chat.md) · [chat-stream-cancel.md](./chat-stream-cancel.md)

---

## 1. Monorepo 一览

```text
memoryOS/
├── apps/api/          Python FastAPI（业务 API、LangGraph、ETL）
├── apps/web/          Next.js 15 BFF + 聊天 UI
├── packages/shared/   TS 常量/类型（无 React）
├── packages/ui/       共享 React 组件（逐步填充）
├── docs/tech/         工程与领域设计（本文件所在目录）
├── docs/tasks/epics/  EP 故事与验收
├── openspec/          变更 proposal / tasks / specs
└── .cursor/skills/    Agent 工作流（work-next、codebase-orient 等）
```

| 应用 | 本地默认 | 说明 |
|:-----|:---------|:-----|
| API | `:8000` | `apps/api`，Conda/venv + Uvicorn |
| Web | `:3000` | `apps/web`，`pnpm dev:web`（Turbopack） |

前后端 **仅 HTTP**；Web 浏览器 **不直连** FastAPI（经 BFF `/api/*`）。

---

## 2. 分层约定（必记）

### 2.1 后端（FastAPI）

```text
HTTP  Request
  ↓
app/api/v1/*.py       路由：薄；Depends 鉴权/限流；不写业务
  ↓
app/services/*.py     业务编排、事务边界
  ↓
app/repositories/*.py  数据访问
  ↓
app/models/*.py       SQLAlchemy ORM
```

**LangGraph**（Agent / RAG 检索）在 `app/graphs/`，由 `ChatService` / `ChatGraphRunner` 调用。

**DB 会话原则（Chat SSE 等长连接）**：

- **禁止**在 SSE 路由上使用 `Depends(get_db)` / `Depends(get_redis)`（yield 依赖会占满整段流式生命周期）。
- 用 `async with AsyncSessionLocal()` **短会话**；Graph 节点用 `graph_db_session(config)` **按 node 开连接**。
- 详见 [chat-rag-stream.md](./chat-rag-stream.md)、博客式复盘：`shit-fastapi-depend-redis`（个人站）。

### 2.2 前端（Next.js）

```text
app/**/page.tsx       页面（薄）
components/**         UI
hooks/**              客户端逻辑（use-chat-session 等）
lib/**                纯函数、BFF 上游、SSE 解析
app/api/**/route.ts   BFF Route Handler（代理 FastAPI）
stores/**             Zustand
```

---

## 3. Chat 全链路（最重要）

用户发消息 → 助手流式回复，**跨三层**：

```text
┌──────────────────────────────────────────────────────────────────┐
│ Browser                                                          │
│  MinimalChat → useChatSession → DefaultChatTransport             │
│       POST /api/chat  (Bearer JWT)                               │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ Next BFF  apps/web/app/api/chat/route.ts                         │
│  fetchMemoryosChatCompletion() → FastAPI                         │
│  memoryosSseResponseToDataStream()  SSE → AI SDK UI stream       │
│  lib/memoryos-upstream.ts · lib/sse-frames.ts                    │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ FastAPI  apps/api/app/api/v1/chat.py                             │
│  prepare（短 DB）→ StreamingResponse(event_generator)            │
│  stream_db（短 DB）→ ChatService.stream_completion_events        │
│  finalize → done SSE；detached memory/summary 后台任务           │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ ChatGraphRunner  apps/api/app/graphs/runner.py                   │
│  retrieve / load_user_memories / call_model / execute_tools …    │
│  节点内 graph_db_session，不借 SSE 会话                          │
└──────────────────────────────────────────────────────────────────┘
```

### 3.1 关键文件索引（Chat）

| 环节 | 路径 |
|:-----|:-----|
| API 路由 | `apps/api/app/api/v1/chat.py` |
| 业务编排 | `apps/api/app/services/chat_service.py` |
| Graph 运行 | `apps/api/app/graphs/runner.py` · `chat_graph.py` |
| 节点 DB 作用域 | `apps/api/app/graphs/db_scope.py` |
| RAG 检索节点 | `apps/api/app/graphs/nodes/retrieve.py` |
| Memory 加载节点 | `apps/api/app/graphs/nodes/load_user_memories.py` |
| Tool 执行节点 | `apps/api/app/graphs/nodes/execute_tools.py` |
| 注入防护中间件 | `apps/api/app/middleware/injection_guard.py` |
| JWT（SSE 用 id-only） | `apps/api/app/core/deps.py` → `get_current_user_id` |
| BFF 路由 | `apps/web/app/api/chat/route.ts` |
| SSE → UI stream | `apps/web/lib/memoryos-upstream.ts` |
| SSE 帧解析 | `apps/web/lib/sse-frames.ts` |
| 聊天 Hook | `apps/web/hooks/use-chat-session.ts` |
| 聊天 UI | `apps/web/components/minimal-chat.tsx` |
| Stop/Cancel BFF | `apps/web/app/api/chat/cancel/route.ts` |

### 3.2 FastAPI SSE 事件 → BFF 映射

| SSE `event` | 含义 | BFF 产出（AI SDK） |
|:------------|:-----|:-------------------|
| `start` | `stream_id` | 响应头 `X-Stream-Id`；generator 内可 skip 重复 |
| `sources` | RAG 命中 | `data-rag-sources` |
| `tool_call` / `tool_result` | ReAct 工具轮 | 对应 data parts；文本段需 `text-end` 再插工具 |
| `token` | 增量文本 | `text-delta`（BFF 侧可合并 batch） |
| `done` | `message_id` | `message-metadata` + `finish` |
| `error` | 失败 | `controller.error` |

协议细节：[chat-rag-stream.md](./chat-rag-stream.md) · 单测 `apps/web/tests/unit/test_memoryos_data_stream.test.ts`

### 3.3 改 Chat 时先问

1. 动的是 **API / BFF / UI** 哪一层？
2. 是否 **长连接**？→ 检查 Depends、BackgroundTasks、middleware `receive`
3. 是否要跑 harness：`apps/api/tests/harness/test_chat_sse_contract.py`

---

## 4. 按领域找代码

| 领域 | 入口 / 服务 | 文档 |
|:-----|:--------------|:-----|
| 鉴权 JWT | `api/v1/auth.py` · `core/deps.py` · `core/security.py` | BE §鉴权 |
| 会话/消息 CRUD | `api/v1/conversations.py` · `conversation_service.py` | EP03 |
| RAG 知识库 | `knowledge_*` · `graphs/nodes/retrieve.py` | [rag-embedding-chunking.md](./rag-embedding-chunking.md) |
| 长期记忆 | `services/memory/` · `load_user_memories` 节点 | [memory-system.md](./memory-system.md) |
| Agent / Tools | `tools/` · `execute_tools` · `runner` ReAct | [agent-langgraph.md](./agent-langgraph.md) |
| 限流 | `core/rate_limit.py` | [rate-limit-audit.md](./rate-limit-audit.md) |
| Token 配额 | `token_quota_service.py` · `api/v1` usage | EP09 |
| 安全/注入 | `middleware/injection_guard.py` · `services/security/` | [chat-security.md](./chat-security.md) |
| 世界杯 Demo 数据 | `api/v1/worldcup.py` · `models/worldcup/` · `etl/worldcup/` | [worldcup-data-model.md](./worldcup-data-model.md) |

---

## 5. 测试在哪里

| 类型 | 路径 | 何时跑 |
|:-----|:-----|:-------|
| API 单测 | `apps/api/tests/unit/` | 改 service/repo/graph |
| API harness（契约） | `apps/api/tests/harness/` | **改 API 行为必跑**相关 contract |
| Web 单测 | `apps/web/tests/unit/` | 改 `lib/`、hooks |
| 根目录 | `pnpm test` / `pytest` | 见各 package README |

Chat 相关 harness 示例：`test_chat_sse_contract.py` · `test_rag_chat_contract.py` · `test_chat_security_contract.py`

---

## 6. OpenSpec / Agent 工作流

| 步骤 | 位置 |
|:-----|:-----|
| 提变更 | `openspec/changes/<name>/` · skill `openspec-propose` |
| 人审 tasks | `tasks.md` §0 · [task-review-gate](../../.cursor/skills/work-next/task-review-gate.md) |
| 实现单 task | skill `work-next` / `openspec-apply-change` |
| **改前 orient** | skill **`codebase-orient`** · **本文件** |

---

## 7. 快速 grep 关键词

| 想找 | 建议搜 |
|:-----|:-------|
| SSE 流式 | `stream_completion_events` · `StreamingResponse` · `memoryosSseResponseToDataStream` |
| 取消/Stop | `cancel_stream` · `StreamCancelCache` · `drainThenAbort` |
| Embedding | `EmbeddingService` · `embedding_cache` |
| LangGraph 配置 | `ChatGraphRunner` · `agent_tools_enabled` |
| 环境变量 | `apps/api/app/core/config.py` · `.env.example` |

---

## 8. 更新日志

| 日期 | 变更 |
|:-----|:-----|
| 2026-06-18 | 初版：Chat 全链路、SSE/DB 原则、领域索引；配合 `.cursor/skills/codebase-orient` |
