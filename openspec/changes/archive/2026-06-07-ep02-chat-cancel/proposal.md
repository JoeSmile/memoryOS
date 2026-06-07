## Why

`ep02-chat-dedup` 已解决发送幂等、regenerate 与 **interrupted 落库**，但用户点「停止」后服务端仍可能继续消费 LangChain/OpenAI 流式 HTTP，产生多余 token 计费。需要在 HTTP abort 之外增加 **可寻址的 cancel 信号** 与 **上游生成器硬断开**，并保留 dedup 已交付的 UI/DB 中断态语义。

## What Changes

- SSE 流开始时下发 `stream_id`（`start` 事件或响应头），供 cancel API 与 Redis 协调。
- Redis `stream_cancel:{stream_id}` + 活跃流注册；token 循环双检 `is_disconnected()` **或** cancel 标记。
- 新增 `POST /api/v1/chat/completions/cancel`（JWT、会话归属、幂等设标）。
- `ChatGraphRunner` / `call_model` 改真流式 + `finally: aclose()`；断开或 cancel 时停止上游。
- 前端 `stop()`：`AbortController` + fire-and-forget cancel API；BFF 补 `ReadableStream.cancel` → 上游 abort 链路。
- Harness：mid-stream disconnect + cancel-only 契约；L02 §4（SSE）与 EP02 计费边界文档。

**Non-Goals（本 change）：**

- 不重做 `ep02-chat-dedup`（`client_message_id`、regenerate、interrupted 展示）。
- 不实现「继续生成」；中断后仍用重新生成 / 新发送。
- 不保证所有供应商 100% 停计费（文档化边界）。

## Capabilities

### New Capabilities

- `chat-stream-cancel`: Cancel API、Redis cancel 标记、活跃流注册、runner 上游断开。

### Modified Capabilities

- `chat-sse`: 流开始下发 `stream_id`；断开/cancel 须停止上游 LLM 消费（超越仅停 SSE 读端）。

## Impact

- **API**：`apps/api/app/api/v1/chat.py`、`services/chat_service.py`、`graphs/runner.py`、`graphs/nodes/call_model.py`、新 cancel 路由。
- **Cache**：`apps/api/app/cache/`（stream cancel 键，复用 Redis 基础设施）。
- **Web**：`hooks/use-chat-session.ts`、`app/api/chat/route.ts`、新 BFF cancel 路由、`lib/memoryos-upstream.ts`。
- **Tests**：`tests/harness/test_chat_sse_contract.py`、新 `test_chat_cancel_contract.py`（或扩展现有）。
- **Docs**：`docs/tasks/learning/L02-streaming-langgraph.md` §4、`docs/tasks/epics/EP02-streaming-chat.md`。
- **勿与** `ep02-chat-dedup` 混 PR；依赖 dedup 已 archive 的 interrupted 落库行为。
