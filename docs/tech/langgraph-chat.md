# LangGraph 对话编排（EP02）

> **状态**：Phase 2 学习草稿 — 在 `ep02-langgraph` apply 时扩写为正式版。  
> **学习**：[L02 §5](../tasks/learning/L02-streaming-langgraph.md)  
> **OpenSpec**：[`ep02-langgraph`](../../openspec/changes/ep02-langgraph/)

---

## 1. 为何用 LangGraph（待扩写）

- 业务层不长期裸调 OpenAI HTTP
- State / Node / Edge 可测试、可扩展（EP05 Agent）

## 2. ChatState（待扩写）

- `messages`：多轮消息
- `user_id`：鉴权用户

## 3. 最小图（待扩写）

```text
START -> call_model -> END
```

## 4. 流式与 SSE（待扩写）

- `stream_tokens()` → `ep02-chat-sse` 消费

## 5. LangSmith（待扩写）

- `LANGCHAIN_TRACING_V2`、`LANGCHAIN_API_KEY`、`LANGCHAIN_PROJECT`
