## Why

`ep04-rag-chat` 已在 FastAPI 发出 SSE `sources` 事件，但 Next.js BFF 的 `memoryosSseResponseToTextStream` **只转发 `token`**，浏览器 `/chat` 页无法展示结构化引用；刷新后引用也丢失（V1 依赖 Markdown `## 参考来源` 脚注）。本 change 升级 BFF 为 AI SDK Data Stream、前端 citation chips，并将 `rag_sources` 持久化到 `messages.metadata`，完成 EP04 Story 4.6 结构化溯源 slice。

## What Changes

- **BFF**：`memoryos-upstream.ts` 新增 SSE → AI SDK Data Stream 转换（解析 `sources`、`done`；保留 Stop/cancel `drainThenAbort` 语义）。
- **BFF route**：`/api/chat` 响应从 `text/plain` 改为 Data Stream；`useChat` 从 `TextStreamChatTransport` 切换为 Data Stream transport。
- **前端 UI**：助手消息下方 **引用 chip 列表**（external_id、collection、score tooltip）；流式中 sources 先于 token 展示。
- **API 持久化**：Alembic 增加 `messages.metadata` JSONB；`finalize_completion_stream` 写入 `{ "rag_sources": [...] }`；列表 API 返回 metadata。
- **溯源双写（人审已定）**：保留 RAG prompt 的 Markdown `## 参考来源` + citation chips；本 change **不改** `rag_chat.py`。
- **Chip 交互（人审已定）**：hover tooltip；click → Popover 展示 `content_preview`（≤240 字）与元数据；**不跳转**（全文 / 知识库详情留 follow-up）。
- **无命中（人审已定）**：无 sources → 无 chips；靠 no-hit 助手文案；「别的渠道查」不在本 change，留 **EP05 Agent Tool**。
- Harness / unit：扩展 RAG chat 或 messages 契约；BFF converter 单测。
- 更新 `docs/tasks/epics/EP04-rag.md` Story 4.6 structured chips 项；`docs/tech/chat-rag-stream.md` 状态。

**Non-Goals（本 change 不做）：**

- 改 FastAPI SSE 事件形状（沿用 V1 `sources` / `done.data.sources`）
- Hybrid / 重排 / Query 改写（EP04-03）
- 知识库上传页（Story 4.1–4.2）
- Playwright E2E（可用 route handler 单测 + Harness 直连 API）
- LangSmith RAG span（EP04 Story 4.7 方向）

## Capabilities

### New Capabilities

- （无独立 capability；持久化归入 `core-schema` + `rag-chat`）

### Modified Capabilities

- `chat-ui`: Data Stream 消费、结构化 citation chips、历史消息 metadata 渲染
- `chat-sse`: `done.data.sources` 与 message 持久化绑定语义（API 侧 finalize）
- `rag-chat`: 助手 message 持久化 `rag_sources` metadata
- `core-schema`: `messages.metadata` JSONB 列

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/web/lib/` | `sse-frames.ts`、`memoryos-upstream.ts`、`chat-types.ts` |
| `apps/web/app/api/chat/` | Data Stream 响应 |
| `apps/web/hooks/` | `use-chat-session.ts` transport |
| `apps/web/components/chat/` | citation chips UI |
| `apps/api/alembic/` | `messages.metadata` migration |
| `apps/api/app/models/`、`schemas/` | Message metadata |
| `apps/api/app/services/chat_service.py` | finalize 写 metadata |
| `apps/api/tests/harness/` | metadata / RAG 契约扩展 |
| `openspec/specs/` | delta `chat-ui`、`chat-sse`、`rag-chat`、`core-schema` |
| 依赖 | 无新 npm/pip 包；对齐现有 `ai` ^6 / `@ai-sdk/react` ^3 |
