## Why

`ep02-chat-ui` 聊天壳 MVP 仅依赖 `isStreaming` 软防护；连点发送、网络重试或 regenerate 会导致 **duplicate user/assistant 行**。需要在 EP04 前补齐 **客户端幂等键 + 服务端去重**，并将 regenerate 与误触双发分离。

## What Changes

- 前端：`isSending` 锁；每条 user 发送附带 `client_message_id`（UUID）；regenerate 走 `regenerate` flag。
- BFF `/api/chat`：透传 `client_message_id` / `regenerate` 至 FastAPI。
- API：`ChatCompletionRequest` 扩展；`messages.client_message_id` + `completion_status`；幂等 + regenerate 档 B；**stop/关页时 partial assistant 落库（interrupted）**。
- Harness：重复 `client_message_id`、regenerate 契约测试。
- 文档：L02 §1「防止重复提交」、EP02 follow-up 勾选。

**Non-Goals（本 change）：** 全链路 LLM cancel（见 `ep02-chat-cancel`）、网络异常重试 UI、会话标题自动生成。

## Capabilities

### New Capabilities

- `chat-message-dedup`: 客户端幂等键、服务端去重、regenerate 不 duplicate user turn。

### Modified Capabilities

- `chat-sse`: `POST /chat/completions` 请求体与幂等/regenerate 行为。
- `core-schema`: `messages` 表增加可选 `client_message_id` 与唯一索引。

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/alembic/versions/` | 新 migration |
| `apps/api/app/models/message.py` | 新列 |
| `apps/api/app/schemas/message.py` | 请求体扩展 |
| `apps/api/app/services/chat_service.py` | 幂等 + regenerate |
| `apps/api/tests/harness/` | 新/扩契约 |
| `apps/web/hooks/use-chat-session.ts` | isSending + client_message_id |
| `apps/web/app/api/chat/route.ts` | body 透传 |
| `docs/tasks/learning/L02-streaming-langgraph.md` | §1 落地勾 |
