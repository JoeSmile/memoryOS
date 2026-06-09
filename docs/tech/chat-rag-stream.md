# 聊天 RAG 流式协议与 BFF 升级路线

> **状态**：✅ **`ep04-rag-chat-stream` 已落地**（BFF Data Stream + citation chips + `metadata.rag_sources`）  
> **关联 OpenSpec**：[`ep04-rag-chat-stream`](../../openspec/changes/ep04-rag-chat-stream/) · 前置 [`ep04-rag-chat`](../../openspec/changes/archive/2026-06-08-ep04-rag-chat/)（V1 Markdown 溯源）  
> **相关**：[聊天 Stop/Cancel](./chat-stream-cancel.md) · [RAG 切块/Embedding](./rag-embedding-chunking.md) · [EP04 史诗](../tasks/epics/EP04-rag.md) Story 4.6

---

## 1. 当前架构（`/chat` 页）

```text
FastAPI  POST /api/v1/chat/completions
  SSE JSON 帧：start → (sources?) → token* → done | error
       ↓
Next.js BFF  POST /api/chat
  memoryosSseResponseToDataStream()
       ↓
AI SDK UI message stream（data parts + text deltas）
       ↓
DefaultChatTransport + useChat
       ↓
UIMessage.parts = data-rag-sources? + text
  + messages.metadata.rag_sources（刷新后）
```

### 1.1 BFF 对各 SSE 事件的处理

| 事件 | FastAPI 含义 | BFF 行为 | 到达浏览器？ |
|:-----|:-------------|:---------|:-------------|
| `start` | 下发 `stream_id` | 回调 `onStreamId`；响应头 `X-Stream-Id` | 间接（Stop/cancel） |
| `sources` | RAG 检索命中 | **`data-rag-sources` data part** | ✅ |
| `token` | 模型增量文本 | `text-start` / `text-delta` / `text-end` | ✅ |
| `done` | `message_id`、可选 `sources` | `message-metadata` + `finish` | ✅ |
| `error` | 流失败 | `controller.error` | ✅ |

关键代码：`apps/web/lib/memoryos-upstream.ts` · `apps/web/lib/sse-frames.ts` · `apps/web/hooks/use-chat-session.ts`。

### 1.2 产品能力（升级后）

| 能力 | 经 BFF（`/chat` 页） | 直连 API / Harness |
|:-----|:---------------------|:-------------------|
| 流式回答正文 | ✅ | ✅ |
| 结构化引用（external_id、score、snippet） | ✅ | ✅ |
| Citation chips（Popover preview） | ✅ | N/A（Web UI） |
| 刷新后 structured sources | ✅（`metadata.rag_sources`） | ✅ |
| Markdown `## 参考来源` 双写 | ✅（prompt 保留） | N/A |

**Stop/Cancel**：仍走 `drainThenAbort` / `clientStopped`；见 [chat-stream-cancel.md](./chat-stream-cancel.md) §6。

---

## 2. 历史：`ep04-rag-chat` V1 权宜方案

V1 **不改 BFF**，用 Markdown 脚注完成首 slice（已 archive）：

1. **后端**：retrieve 后发 SSE `sources`（Harness / 直连 API 可测）。
2. **Prompt**：正文末尾 `## 参考来源`。
3. **前端**：`markdown-body` 折叠块。

**局限**：BFF 仅转发 token；刷新后无 structured metadata。由本 change 解决。

---

## 3. 升级目标（`ep04-rag-chat-stream` — 已完成）

### 3.1 产品目标

- [x] 流式过程中 **先于 token** 展示 citation chips。
- [x] 助手消息绑定 **结构化 `rag_sources[]`**（data part + DB metadata）。
- [x] **刷新 / 重进会话** 从 `GET .../messages` 渲染 chips。
- [x] Stop、duplicate、interrupted 行为与现网一致（Harness + 单测覆盖 converter）。

### 3.2 协议映射

| 上游 SSE | 下游（浏览器） | 说明 |
|:---------|:---------------|:-----|
| `start` | 不变 | `stream_id` / cancel |
| `sources` | `data-rag-sources` | `{ items: RagSourceItem[] }` |
| `token` | text delta | 与现网相同 |
| `done` | `message-metadata` + `finish` | `messageId` + 可选 `ragSources` |
| `error` | error part | 与现网相同 |

`RagSourceItem` 字段（与 API `KnowledgeChunkHit` 对齐）：

```typescript
type RagSourceItem = {
  external_id: string;
  collection: string;
  entity_type?: string | null;
  score: number;
  content_preview: string; // 截断 snippet，非全文
};
```

---

## 4. 实施阶段（完成状态）

| Phase | 内容 | 状态 |
|:------|:-----|:-----|
| 0 | OpenSpec `ep04-rag-chat-stream` + delta specs | ✅ |
| 1 | BFF SSE → Data Stream（`memoryosSseResponseToDataStream`） | ✅ |
| 2 | Citation chips UI + store（双写 Markdown） | ✅ |
| 3 | `messages.metadata` + list API + finalize 写入 | ✅ |
| 4 | 测试：`test_memoryos_data_stream.test.ts` + `test_rag_chat_contract.py` metadata | ✅ |

---

## 5. 关键设计决策（人审已定）

| 问题 | 结论 |
|:-----|:-----|
| BFF 协议 | **AI SDK Data Stream** |
| 历史消息引用 | **DB `metadata.rag_sources`** + UI chips |
| Prompt Markdown 脚注 | **保留双写**（chips + `## 参考来源`） |
| `done` 与 `sources` | **双发**：`sources` 早展示，`done` 绑定 id |
| Chip 交互 | Popover preview，**不跳转** |
| 无命中 | 无空状态 chip；外部检索留 EP05 Tool |
| Cancel | **不变**；data stream 不破坏 drain |

---

## 6. 文件索引

| 层 | 路径 |
|:---|:-----|
| API SSE + 持久化 | `apps/api/app/services/chat_service.py` · `models/message.py` |
| BFF | `apps/web/app/api/chat/route.ts` |
| SSE / Data Stream | `apps/web/lib/sse-frames.ts` · `memoryos-upstream.ts` |
| 聊天 Hook / Store | `apps/web/hooks/use-chat-session.ts` · `stores/chat-store.ts` |
| UI | `apps/web/components/chat/chat-message.tsx` · `rag-source-chip.tsx` |
| 单测 | `apps/web/tests/unit/test_memoryos_data_stream.test.ts` |
| Harness | `apps/api/tests/harness/test_rag_chat_contract.py` |
| OpenSpec | `openspec/changes/ep04-rag-chat-stream/` |

---

## 7. 变更记录

| 日期 | 说明 |
|:-----|:-----|
| 2026-06-08 | 初稿：`ep04-rag-chat` propose 时记录 BFF token-only 限制与 Data Stream 升级路线 |
| 2026-06-08 | **`ep04-rag-chat-stream` 落地**：Data Stream BFF、citation chips、`metadata.rag_sources`；Harness 42 + web unit 3 |
