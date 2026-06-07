# LangGraph 对话编排（EP02）

> **状态**：`ep02-langgraph` 已落地（2026-06）— 与 `apps/api/app/graphs/` 对齐。  
> **学习**：[L02 §5–§7](../tasks/learning/L02-streaming-langgraph.md)  
> **OpenSpec**：[`ep02-langgraph`（archived）](../../openspec/changes/archive/2026-06-03-ep02-langgraph/) · 下游
> [`ep02-chat-sse`](../../openspec/changes/ep02-chat-sse/)

---

## 1. 为何用 LangGraph

| 做法                                          | 问题                                                         |
| :-------------------------------------------- | :----------------------------------------------------------- |
| Router/Service 里 `while` + httpx 直连 OpenAI | 分支、重试、状态、可观测分散；难单测；违反项目「不裸调」原则 |
| 仅 LangChain `Runnable` 链                    | 多轮 + 条件分支 + 后续 Agent 时编排不清晰                    |

**选择 LangGraph 的原因：**

- **显式 State**：`messages`、`user_id` 等在图上可读、可测。
- **Node / Edge**：`call_model` 独立；EP05 再加 `retrieve` / `tool`
  节点不改 HTTP 契约。
- **流式一等公民**：`astream_events` / `stream_mode` 映射到 SSE `token` 事件。
- **可观测**：LangChain 调用自动进 LangSmith；图内细粒度用 TruLens（联调，见 §8）。

本阶段
**Non-Goals**（`ep02-langgraph`）：工具调用、RAG、记忆写入、checkpoint 落库、SSE
HTTP 层。

---

## 2. 在 MemoryOS 中的位置

```text
POST /api/v1/chat/completions   ← ep02-chat-sse（HTTP + SSE）
        │
        ▼
ChatService                     ← 持久化 user message、StreamCache、assistant 落库
        │
        ▼
ChatGraphRunner.stream_tokens() ← ep02-langgraph（本文档）
        │
        ▼
compiled StateGraph             ← call_model（OpenAI 或 Mock）
```

**分层**（见 [BE-engineering.md](./BE-engineering.md) §3）：

- `api/v1/chat.py`：不 import LangGraph。
- `services/chat_service.py`：组 state、调 runner、处理取消。
- `app/graphs/`：图定义、节点、runner；**无 SQL**。

---

## 3. ChatState

使用 LangGraph `StateGraph` + `Annotated` 累加消息（与 LangChain
message 类型对齐）。

| 字段       | 类型                            | 说明                                             |
| :--------- | :------------------------------ | :----------------------------------------------- |
| `messages` | `Annotated[list, add_messages]` | 多轮历史 + 本轮 user；节点返回 assistant 增量    |
| `user_id`  | `UUID` 或 `str`                 | 来自 JWT `get_current_user`，便于日志/trace 关联 |

**与 DB 的关系：**

- **真相源**：PostgreSQL `messages` 表（`role` / `content` /
  `conversation_id`）。
- **图内 state**：由 `ChatService`
  在每次请求前从 DB 加载最近 N 条（首版可全量会话；EP06 再做裁剪）。
- 图执行 **不** 直接写库；落库在 Service 的 `done` 之后（`ep02-chat-sse`）。

实现见 [`apps/api/app/graphs/chat_state.py`](../../apps/api/app/graphs/chat_state.py)。
`messages` 使用 `add_messages` reducer：节点返回 `{"messages": [AIMessage(...)]}` 时 **追加**，非整表替换。

---

## 4. 最小图：Node 与 Edge

### 4.1 拓扑（Phase 4）

```text
START ──► call_model ──► END
```

| 节点         | 输入             | 输出（partial state）                                  |
| :----------- | :--------------- | :----------------------------------------------------- |
| `call_model` | `state.messages` | 追加 assistant `AIMessage`（流式时由 runner 拆 token） |

| 边                   | 类型 | 说明                                    |
| :------------------- | :--- | :-------------------------------------- |
| `START → call_model` | 固定 | 唯一入口                                |
| `call_model → END`   | 固定 | 无 `should_continue`；EP05 再引入条件边 |

### 4.2 `call_model` 行为

1. 读取 `state.messages`（含 system / history / 当前 user）。
2. **有 `OPENAI_API_KEY`**：`ChatOpenAI` streaming，LangSmith 自动 trace。
3. **无 Key**：`MockModelNode` 产出确定性 token 序列（如
   `["你","好","！"]`），**零外网**，Harness/CI 必走此路径。

节点函数 **纯函数风格**：只返回 partial state，不 mutating 全局变量。

---

## 5. 目录与模块（已实现）

| 路径                             | 职责                                                         |
| :------------------------------- | :----------------------------------------------------------- |
| `app/graphs/chat_state.py`       | `ChatState` TypedDict                                        |
| `app/graphs/chat_graph.py`       | `build_chat_graph()` → `compiled`                            |
| `app/graphs/nodes/call_model.py` | 真模型节点                                                   |
| `app/graphs/nodes/mock_model.py` | Mock 流式节点                                                |
| `app/graphs/runner.py`           | `ChatGraphRunner.stream_tokens(state) -> AsyncIterator[str]` |
| `tests/unit/test_chat_graph.py`  | mock 流式、无网络                                            |

依赖（`requirements.txt`，task
1.1）：`langgraph`、`langchain-openai`、`langchain-core`；版本锁在 change 内。

---

## 6. 流式策略

### 6.1 对外契约

Runner 对外只暴露 **异步字符流**，供 SSE 消费：

```python
async def stream_tokens(self, state: ChatState) -> AsyncIterator[str]:
    ...
```

- 每个 `str` 为 **增量 token**（可为单字或短片段，由模型 chunk 决定）。
- 流结束即 iterator 完成；**不** 在 runner 内写 SSE 格式。

### 6.2 图内实现

[`ChatGraphRunner.stream_tokens`](../../apps/api/app/graphs/runner.py)：

- **Mock**（无 `OPENAI_API_KEY`）：`mock_stream_tokens()` → `["你","好","！"]`
- **真模型**：`graph.astream_events(..., version="v2")`，过滤
  `on_chat_model_stream` 的 `chunk.content`

`ChatService`（`ep02-chat-sse`）消费该 iterator 并写 SSE / `StreamCache`。

### 6.3 与 SSE 事件映射

| Runner                    | SSE `data` 行                                                         |
| :------------------------ | :-------------------------------------------------------------------- |
| 每个 token `str`          | `{"event":"token","data":{"content":"<str>"}}`                        |
| iterator 结束 + DB 落库后 | `{"event":"done","data":{"message_id":"...","stream_id":"..."}}`      |
| 上游失败                  | `{"event":"error","data":{"code":50002,"message":"upstream_failed"}}` |

HTTP 层在 SSE 开始前失败 → 统一 `{ code, message, data }` JSON（非 SSE）。

### 6.4 取消（`ep02-chat-cancel`）

> 完整方案与踩坑：**[`chat-stream-cancel.md`](./chat-stream-cancel.md)**

- **混合 Stop**：浏览器 `AbortController` + `POST .../cancel`（Redis 标记，多 worker 兜底）。
- **Runner**：循环内双检 `is_disconnected()` OR `is_cancelled(stream_id)`，间隔 **250ms**；停止时 `aclose()` 上游。
- **落库**：`finalize_completion_stream` 在 router `finally` 必跑；`interrupted` 保留 partial。
- **用户快照**：cancel 可带 `visible_content`，finalize 截断为「停住时所见」；BFF abort 后只 drain、不继续转发给浏览器。

**与旧稿差异**（`ep02-chat-sse` D4）：断开 / Stop **会**落库 `interrupted`，不再「断开则不落库」。

---

## 7. 并发与隔离

| 坑                         | 规避                                                                                |
| :------------------------- | :---------------------------------------------------------------------------------- |
| 多请求共享同一 `thread_id` | 每请求 `config = {"configurable": {"thread_id": "<conversation_id 或 stream_id>"}}` |
| 节点内写全局单例           | 状态只在 `ChatState`；模型客户端可进程级单例但无请求级可变字段                      |

首版 **不启用** LangGraph checkpoint 持久化；`thread_id` 仅用于 trace/调试隔离。

---

## 8. 可观测

### 8.1 LangSmith（主路径）

本地 `.env`（勿提交密钥；见 `apps/api/.env.example`）：

```bash
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=memoryOS-dev
```

（若团队仍用旧变量名 `LANGCHAIN_TRACING_V2` /
`LANGCHAIN_API_KEY`，与 LangSmith 文档等价，择一统一即可。）

| 用途                           | 操作                              |
| :----------------------------- | :-------------------------------- |
| 看延迟在 prompt / model / 网络 | 打开 Run 树，对比子 Run 耗时      |
| dev / prod 分离                | 不同 `LANGSMITH_PROJECT`          |
| CI / 压测                      | 关 tracing 或专用 key，避免额度爆 |

### 8.2 TruLens（图内联调，可选）

见 [L02 §7](../tasks/learning/L02-streaming-langgraph.md)。**不替代**
LangSmith；用于看清 **GRAPH_NODE / @task**。

| 场景                      | 工具               |
| :------------------------ | :----------------- |
| 线上 / 团队统一 trace     | LangSmith          |
| 节点级排障、多 Agent 预研 | TruLens `TruGraph` |

沙箱（待建）：`apps/api/scripts/sandbox_trulens_langgraph.py`。

---

## 9. Mock 与真模型

| 条件                        | 路径                                                       |
| :-------------------------- | :--------------------------------------------------------- |
| `OPENAI_API_KEY` 未设置或空 | `MockModelNode`，确定性 token，**无网络**                  |
| Key 已设置                  | `ChatOpenAI` + `OPENAI_MODEL` + `OPENAI_BASE_URL`（百炼 `qwen-turbo` 必填 DashScope 兼容地址） |

```bash
# 仅跑图单测（ep02-langgraph 3.1）
cd apps/api && pytest tests/unit/test_chat_graph.py -q
```

Harness（`ep02-chat-sse`）依赖同一 mock 路径，保证 `pnpm test:api:harness`
无 Key 仍绿。

---

## 10. 测试策略

| 层级    | 文件                                      | 断言                                         |
| :------ | :---------------------------------------- | :------------------------------------------- |
| Unit    | `tests/unit/test_chat_graph.py`           | mock 流式 ≥1 token；完整 iterator；无 socket |
| Harness | `tests/harness/test_chat_sse_contract.py` | SSE 帧形状；由 chat-sse change 添加          |
| 手工    | LangSmith UI                              | 有 Key 时一次 invoke 可见 trace              |

---

## 11. 演进路线（不在本阶段实现）

| 史诗       | 图演进                                                 |
| :--------- | :----------------------------------------------------- |
| EP04 RAG   | 增加 `retrieve` 节点 → `call_model`                    |
| EP05 Agent | 条件边 `should_continue`、tool 节点、`recursion_limit` |
| EP06 记忆  | state 增加 memory 引用；prompt 裁剪策略                |
| EP02+      | checkpoint / 中断恢复（需存储选型）                    |

---

## 12. 验收清单

- [x] 本文档与代码对齐
- [x] `ep02-langgraph` 1.1–3.2（config、图、runner、单测）
- [ ] `ep02-chat-sse` 将 `ChatService` 接到 `stream_tokens`
- [ ] LangSmith 手工 trace（本地 `LANGSMITH_TRACING=true` + Key，可选）

**验证命令（2026-06）：**

```bash
cd apps/api && pytest tests/unit/test_chat_graph.py -q   # 2 passed
pnpm test:api:harness                                     # 9 passed
```

---

## 参考

| 主题                | 链接                                                                        |
| :------------------ | :-------------------------------------------------------------------------- |
| LangGraph           | https://langchain-ai.github.io/langgraph/                                   |
| LangSmith           | https://docs.smith.langchain.com                                            |
| TruLens · LangGraph | https://www.trulens.org/component_guides/instrumentation/langgraph/         |
| 项目 SSE 设计       | [`ep02-chat-sse/design.md`](../../openspec/changes/ep02-chat-sse/design.md) |
