## Context

- **现状**：FastAPI 在 RAG 路径发 `start → sources? → token* → done`；BFF 仅 `token` → `TextStreamChatTransport` → `useChat` text parts。V1 UI 靠 Markdown `## 参考来源` 折叠块。
- **约束**：Stop/Cancel 行为必须与 [chat-stream-cancel.md](../../../docs/tech/chat-stream-cancel.md) 兼容（`drainThenAbort`、`X-Stream-Id`、duplicate 409）。
- **依赖**：`ep04-rag-chat` ✅ archive；API `sources` 形状已稳定。
- **参考**：[chat-rag-stream.md](../../../docs/tech/chat-rag-stream.md) §3–§6。

## Goals / Non-Goals

**Goals:**

- BFF 将 `sources` / `done` 转为 AI SDK Data Stream parts，浏览器可绑定 structured sources。
- 流式：sources 先于 token 展示 citation chips。
- 刷新后：从 `GET .../messages` 的 `metadata.rag_sources` 渲染 chips。
- Harness 覆盖 metadata 持久化；cancel/regenerate 回归不回归。

**Non-Goals:**

- 修改 LangGraph retrieve 或 **去掉** RAG prompt 的 Markdown `## 参考来源`（本 change **保留双写**）
- BFF 以外的客户端（移动端 SDK）
- 全文 chunk 展示（仅 `content_preview` snippet）

## Decisions

### D1: BFF 协议 — AI SDK Data Stream

- 新增 `memoryosSseResponseToDataStream()`，输出 AI SDK v6 data stream 帧。
- `sources` → custom data part（建议 type `data-rag-sources`，payload `{ items: RagSourceItem[] }`）。
- `token` → text delta（与现网相同）。
- `done` → message metadata part（`messageId` + 可选 `sources` 摘要）。
- **替代**：继续 text/plain + 自定义前缀 — 与 `useChat` 生态不一致，弃用。

### D2: Transport 切换

- `use-chat-session.ts`：`TextStreamChatTransport` → `DefaultChatTransport`（或 AI SDK 6 等价 Data Stream transport，对齐 `ai` 包文档）。
- BFF `Content-Type` 改为 data stream MIME（与 `@ai-sdk/react` 版本一致）。

### D3: 持久化 — `messages.metadata` JSONB

```json
{ "rag_sources": [{ "external_id", "collection", "entity_type?", "score", "content_preview" }] }
```

- 在 `finalize_completion_stream`（或同等路径）与 assistant row 同一事务写入。
- 无命中（无 `sources` SSE）→ `metadata` null 或 `{}`。
- **回滚**：migration nullable；旧消息 null → 仅显示正文。

### D4: UI — chips + Markdown 双写（人审已定）

- **Structured chips**：来自 data part / `metadata.rag_sources`（主展示，先于 token）。
- **Markdown 脚注**：保留 `rag_chat` prompt 要求的 `## 参考来源`；`markdown-body` 现有折叠样式 **不删、不隐藏**。
- **并存**：同一条消息可同时看到 chips + Markdown 来源块（接受略重复；旧消息无 metadata 时仅靠 Markdown）。
- **本 change 不做**：改 prompt 去掉脚注；chip 跳转 `/knowledge`（Story 4.1 未建）；无命中「去外部查」按钮（→ EP05 Tool）。

### D4b: Chip 交互（人审已定）

- **Hover**：tooltip 一行（`external_id` + 截断 preview）。
- **Click**：Popover / 小面板展示完整 `content_preview`（API 现最多 ~240 字）、`collection`、`score`。
- **不跳转**：无 `/knowledge/{id}` 页；**不**在本 change 加「拉全文 chunk」API（follow-up 可 `GET` by `external_id`）。
- 键盘：chip 可 focus，Enter 同 click 开 Popover。

### D4c: 无 RAG 命中（人审已定）

- **不发** `sources` SSE → **不展示** chips（与 V1 一致）。
- 助手正文走现有 no-hit prompt（诚实说明知识库无相关内容）。
- **不做**「未找到来源，去搜索」类 CTA — 用户改问或切 **Agent + Tool**（EP05 Story 5.3 网页搜索 / 知识库检索工具）。

### D5: Cancel 不变

- `memoryosSseResponseToDataStream` **必须**复用现 `clientStopped`、`drainThenAbort`、`onStreamId` 逻辑（见 cancel 文档 §6.6）。
- Data stream 升级 **不得** 在 client abort 时立即 `abortUpstream` 丢 partial。

### D6: 测试分层

| 层 | 覆盖 |
|:---|:-----|
| unit | `sse-frames` 解析 sources/done；upstream converter mock SSE |
| harness | API：`done` 后 message 含 `metadata.rag_sources`；RAG 有命中 |
| 手动 | `/chat` Stop、regenerate、刷新后 chips |

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| AI SDK 6 data stream API 变更 | 锁版本；converter 单测 |
| 双写 Markdown + chips 略重复 | 人审接受；chips 在上、Markdown 脚注在下；旧消息仅 Markdown |
| migration 锁表 | dev 小表；EP08 维护窗 |
| BFF 改协议破坏旧客户端 | 仅 web BFF；API SSE 不变 |

## Migration Plan

1. `pnpm db:migrate` 部署 metadata 列。
2. 部署 API（写 metadata）。
3. 部署 web（Data Stream BFF + UI）。
4. 回滚：web 回 text stream；metadata 列可留空。

## Open Questions

- [x] 人审：**保留双写** — prompt `## 参考来源` + chips 并存
- [x] 人审：chip **Popover 展示 preview**，不跳转、不拉全文 API
- [x] 人审：**无命中无空状态 chip**；外部渠道 → EP05 Agent Tool
