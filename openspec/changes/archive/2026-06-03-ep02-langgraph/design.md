## Context

- EP03 JWT、messages 表、StreamCache 已存在。
- `ep02-program` Phase 2 应产出 `langgraph-chat.md` 草稿。
- `ep02-chat-sse` 将把 SSE 接到本图的流式输出。

## Goals / Non-Goals

**Goals:**

- LangSmith：`LANGCHAIN_TRACING_V2=true` 时 trace 可见。
- Graph：`ChatState` 含 `messages: Annotated[list, add_messages]`（或等价）。
- 流式：对外 async generator `stream_tokens(state) -> AsyncIterator[str]`。
- Mock：无 `OPENAI_API_KEY` 时固定 token 序列。
- 每请求 `thread_id` / `configurable` 隔离，避免并发串台。

**Non-Goals:**

- 工具调用、RAG 检索、记忆写入。
- LangGraph checkpoint 落库。
- SSE HTTP 层（在 `ep02-chat-sse`）。

## Decisions

### D1: 包选型

- **选择**：`langgraph` + `langchain-openai` `ChatOpenAI` streaming；LangSmith 通过 LangChain 自动 trace。
- **备选**：自研 httpx — 违反项目原则。

### D2: 图结构（Phase 4 最小）

```text
START -> call_model -> END
```

- `call_model`：读 state.messages，流式写回 assistant 内容到 state。

### D3: Mock 路径

- `settings.openai_api_key` 空 → `MockModelNode` 产出 `["你","好","！"]` 等固定序列。
- Harness 只走 mock。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| 依赖体积大 | 仅 api 包；锁版本 |
| 本地无 Key 无法测真模型 | 文档说明；staging 配 Key |

## Migration Plan

1. `pnpm setup:api` 安装新依赖。
2. 配置 `.env` LangSmith + 可选 OpenAI。
3. unit test 不访问外网。
