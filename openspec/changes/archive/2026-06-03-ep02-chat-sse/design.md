## Context

- **现状**：`conversations` CRUD 存在，通过 query `user_id` 未强制 JWT 绑定；`messages` 表与 `StreamCache` 已有（EP03.3）；`/chat` 为占位页；JWT + `apiFetch` 已就绪。
- **约束**：统一 HTTP 错误体 `{ code, message, data }`；SSE 数据帧内用 **JSON** 描述事件；分层 Router → Service → Repository。
- **依赖**：**必须** `ep02-langgraph` archive；**推荐** `ep03-db-optimize`（[`ep02-program`](../ep02-program/tasks.md) Phase 1）。

## Goals / Non-Goals

**Goals:**

- `POST /api/v1/chat/completions`：`Content-Type: text/event-stream`，Bearer 必填。
- 请求体：`{ "conversation_id": "<uuid>", "content": "<user text>" }`。
- SSE 事件类型：`token`（增量文本）、`done`（含 `assistant_message_id`）、`error`（业务码）。
- 流式过程中 `StreamCache.append`；完成后写入 `messages`（role `assistant`），删除 stream key。
- `GET /api/v1/conversations/{conversation_id}/messages`：按 `created_at` 升序。
- 校验：conversation 属于 `get_current_user`；否则 404/403（统一用 40401 避免泄露）。
- Dev/Harness：走 **LangGraph mock 节点**（与 `ep02-langgraph` 一致），保证 CI 绿。
- 前端：`fetch` + ReadableStream 解析 SSE，`Authorization` 来自 `memoryos_access_token`。

**Non-Goals:**

- 在本 change 内新建 LangGraph 图（在 `ep02-langgraph`）。
- 侧栏多会话 UI、Markdown 渲染、虚拟列表（`ep02-chat-ui`，Phase 7）。
- 会话标题自动生成、Zustand 全局 store。
- 改造所有 `conversations` 列表为仅 JWT（可 follow-up）；本 change 至少 **chat + messages** 路径强制 JWT。

## Decisions

### D1: SSE 路由与事件格式

- **路由**：`POST /api/v1/chat/completions`（对齐 EP02 史诗命名）。
- **帧格式**（每条 `data:` 一行 JSON）：

```json
{"event":"token","data":{"content":"你"}}
{"event":"done","data":{"message_id":"<uuid>","stream_id":"<uuid>"}}
{"event":"error","data":{"code":50002,"message":"upstream_failed"}}
```

- **备选**：WebSocket — 复杂度高，EP02 史诗已定 SSE。

### D2: 上游仅 LangGraph

- **选择**：`ChatService` 只调用 `stream_tokens()` from `ep02-langgraph`；不在本 change 新增 httpx 直连 OpenAI。
- **理由**：符合项目「不裸调」原则；Mock 在 graph 层。

### D3: 鉴权与所有权

- 所有本 change 路由：`user: User = Depends(get_current_user)`。
- `conversation.user_id` 必须等于 `user.id`；否则 `AppException` 40401。
- SSE 请求不从 body 传 `user_id`。

### D4: 断开与取消

- FastAPI `Request.is_disconnected()` 或 `asyncio.CancelledError`：停止读取上游，不提交半条 assistant（或标记失败）；`StreamCache.delete`。

### D5: 前端

- **`lib/sse-client.ts`**：解析 SSE、`onToken`/`onDone`/`onError`、`signal` 传给 `fetch`。
- **`/chat`**：query `?conversation_id=` 或创建会话后跳转；**非** 完整 EP02 布局。
- Token 存储：沿用 `memoryos_access_token`。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| conversations 仍可用 query `user_id` 越权 | 本 change 新路由强制 JWT；列表改造 follow-up |
| OpenAI 费用/密钥 | mock 路径；文档说明仅 dev 配 Key |
| SSE 代理缓冲 | Nginx 需 `X-Accel-Buffering: no`（EP08 文档） |
| 半条 assistant 落库 | 仅 `done` 后 commit；断开则不 insert assistant |

## Migration Plan

1. `pnpm setup:api` 若新增 `httpx` 依赖。
2. `.env` 配置 `OPENAI_API_KEY`（可选）。
3. 无 Alembic 变更（复用 `messages` 表）。
4. Harness 不调用真实 OpenAI。

## Open Questions

- [ ] 是否在 apply 前合并 `ep03-db-optimize` 的「创建会话+首条消息」API？（推荐是）
- [ ] `ep02-chat-ui` 是否复用本 change 的 `/chat` 或新建 `/chat/[id]`？（建议 ui change 再迁路由）
