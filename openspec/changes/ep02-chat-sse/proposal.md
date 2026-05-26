## Why

EP02 需要 **SSE 传输层**：鉴权后发消息、流式 token、落库。须在 **LangGraph 最小图**（`ep02-langgraph`）就绪后实现，由 Graph 驱动上游而非长期裸调 OpenAI/Mock 适配器。

对应 EP02 Program **Phase 5–6**；前置 `ep03-db-optimize`（Phase 1）。

## What Changes

- `POST /api/v1/chat/completions`：SSE；上游 **ChatGraphRunner.stream_tokens**。
- `GET /api/v1/conversations/{id}/messages` + JWT 所有权。
- `ChatService`：user message 持久化 → 调 Graph 流 → `StreamCache` → assistant 落库。
- 前端 Phase 6：`lib/sse-client.ts` + 最小 `/chat`（**非**侧栏完整 UI，属 Phase 7 `ep02-chat-ui`）。
- Harness：`test_chat_sse_contract.py`（mock graph 路径）。

## Capabilities

### New Capabilities

- `chat-sse`: SSE 聊天补全、事件格式、取消与消息持久化。

### Modified Capabilities

- `data-access-layer`: 消息列表；chat 路由 JWT 所有权。
- `jwt-auth`: SSE 需 Bearer。

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/app/api/v1/chat.py` | SSE |
| `apps/api/app/services/chat_service.py` | 调 graphs |
| `apps/web/lib/sse-client.ts` | Phase 6 |
| `tests/harness/test_chat_sse_contract.py` | L1 |

**依赖 change：** `ep03-db-optimize`（推荐）、**`ep02-langgraph`（必须）**  
**后续 change：** `ep02-chat-ui`（Phase 7）
