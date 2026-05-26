## Why

项目要求对话编排走 **LangGraph**，禁止业务层长期裸调 OpenAI。在 SSE/UI 之前需要 **最小可运行图**：State + 单模型节点 + 流式 token 输出，并接 **LangSmith** 可观测。

对应 EP02 Program **Phase 3–4**；阻塞 `ep02-chat-sse` 后端实现。

## What Changes

- 依赖：`langgraph`、`langchain-openai`（或项目选定包）、LangSmith env。
- `apps/api/app/graphs/chat_graph.py`：最小 `StateGraph`（messages、user_id）。
- 节点：`call_model` 流式；无 API Key 时 **mock 节点**（Harness）。
- `ChatGraphRunner` 或 service 封装：`astream_events` → token 回调。
- `docs/tech/langgraph-chat.md` 从 Phase 2 草稿扩写为正式版。
- **不引入**：多工具、条件分支、checkpoint 持久化（EP05）。

## Capabilities

### New Capabilities

- `langgraph-chat`: 最小对话 StateGraph 与流式执行。

### Modified Capabilities

- （无）

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/app/graphs/` | 新目录 |
| `requirements.txt` | langgraph 等 |
| `.env.example` | LangSmith + OpenAI |
| `tests/unit/` | graph mock stream |
| `docs/tech/langgraph-chat.md` | 正式文档 |
