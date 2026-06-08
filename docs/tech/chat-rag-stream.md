# 聊天 RAG 流式协议与 BFF 升级路线

> **状态**：📋 **已记录 · 待 follow-up change**（`ep04-rag-chat` V1 **不实施**）  
> **关联 OpenSpec**：[`ep04-rag-chat`](../../openspec/changes/ep04-rag-chat/)（V1 Markdown 溯源）· 建议后续 change 名 **`ep04-rag-chat-stream`** 或 **`ep02-chat-data-stream`**  
> **相关**：[聊天 Stop/Cancel](./chat-stream-cancel.md) · [RAG 切块/Embedding](./rag-embedding-chunking.md) · [EP04 史诗](../tasks/epics/EP04-rag.md) Story 4.6

---

## 1. 现状：BFF 不是坏了，是「只传 token」

EP02 聊天页路径：

```text
FastAPI  POST /api/v1/chat/completions
  SSE JSON 帧：start → (sources?) → token* → done | error
       ↓
Next.js BFF  POST /api/chat
  memoryosSseResponseToTextStream()
       ↓
text/plain 纯文本流（仅 token.data.content 字符）
       ↓
TextStreamChatTransport + useChat（Vercel AI SDK）
       ↓
UIMessage.parts = text only
```

### 1.1 BFF 对各 SSE 事件的处理

| 事件 | FastAPI 含义 | BFF 行为 | 到达浏览器？ |
|:-----|:-------------|:---------|:-------------|
| `start` | 下发 `stream_id` | 回调 `onStreamId`；响应头 `X-Stream-Id` | 间接（Stop/cancel） |
| `token` | 模型增量文本 | **enqueue 到 TextStream** | ✅ |
| `sources` | RAG 检索命中（`ep04-rag-chat` 新增） | **忽略** | ❌ |
| `done` | `message_id`、可选 `sources` 摘要 | **忽略** | ❌ |
| `error` | 流失败 | `controller.error` | ✅（以异常结束） |

关键代码：`apps/web/lib/memoryos-upstream.ts` 的 `memoryosSseResponseToTextStream` 仅调用 `extractTokenContent`；`apps/web/lib/sse-frames.ts` 无 `sources` / `done` 解析器。

### 1.2 对 RAG 产品的影响

| 能力 | 经 BFF（`/chat` 页） | 直连 API / Harness |
|:-----|:---------------------|:-------------------|
| 流式回答正文 | ✅ | ✅ |
| 结构化引用（external_id、score、snippet） | ❌ | ✅ |
| 引用 chip / 点击溯源 UI | ❌ | 需自建客户端 |
| 刷新后结构化引用 | ❌（且 V1 未写 DB） | ❌ |

**Stop/Cancel 不受影响**：`drainThenAbort`、`clientStopped`、`finalize` 与 token-only 设计兼容；升级协议时 **必须** 回归 [chat-stream-cancel.md](./chat-stream-cancel.md) §6。

---

## 2. `ep04-rag-chat` V1 的权宜方案

V1 **不改 BFF**，用以下组合完成 Demo 与 Story 4.6 首 slice：

1. **后端**：retrieve 后发 SSE `sources`（Harness / 直连 API 可测）。
2. **Prompt**：要求模型在正文末尾输出 Markdown `## 参考来源`（`- [external_id] …`）。
3. **前端**：`markdown-body` / `chat-message` 对该标题区块加样式（小字 / 折叠）。

**优点**：改动小、BFF/cancel 零风险、Markdown 随 token 自然过 BFF。  
**缺点**：引用与正文混在一段 text 里；无法做 chip、score 着色、按 collection 过滤展示；刷新后无法从 metadata 还原结构化 sources。

---

## 3. 升级目标（follow-up change）

### 3.1 产品目标

- 流式过程中 **先于 token** 展示「检索到的 N 条来源」。
- 助手消息绑定 **结构化 `sources[]`**（不依赖正则解析 Markdown）。
- **刷新 / 重进会话** 仍能看见引用（需 DB 持久化）。
- 保持 Stop、duplicate、interrupted 行为与现网一致。

### 3.2 协议目标

在 **不破坏** FastAPI SSE 契约的前提下，BFF 从 **Text Stream** 升级为 **AI SDK Data Stream**（或等价 multi-part stream），至少支持：

| 上游 SSE | 下游（浏览器） | 说明 |
|:---------|:---------------|:-----|
| `start` | 不变 | `stream_id` / cancel |
| `sources` | `data` part `type: rag-sources` | 结构化数组 |
| `token` | text delta | 与现网相同 |
| `done` | finish + `message_id` + 可选 `sources` | 绑定持久化 id |
| `error` | error part | 与现网相同 |

`rag-sources` item 建议字段（与 API `KnowledgeChunkHit` 对齐）：

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

## 4. 实施思路（分阶段）

### Phase 0 — 契约冻结（文档 + OpenSpec）

- propose **`ep04-rag-chat-stream`**（或合并进 EP02 扩展 change）。
- Delta specs：`chat-sse`（`done.data.sources` 必选语义）、`chat-ui`（citation chips）、`rag-chat`（持久化）。
- 在本文件 §6 记录 baseline 行为截图 / Harness 用例 ID。

### Phase 1 — BFF：SSE → Data Stream

**文件**：`apps/web/lib/memoryos-upstream.ts`、`apps/web/app/api/chat/route.ts`、`apps/web/hooks/use-chat-session.ts`

1. 新增 `memoryosSseResponseToDataStream()`（或重构现有函数）：
   - 解析 `sources` → enqueue AI SDK data annotation。
   - `token` → text delta（保留 `clientStopped` / `drainThenAbort` 逻辑，见 cancel 文档 §6.6）。
   - `done` → finish metadata（`message_id`、`sources`）。
2. BFF 响应 `Content-Type` 从 `text/plain` 改为 AI SDK data stream 约定（与 `@ai-sdk/react` 版本对齐）。
3. **回归**：Stop 后 partial 落库、duplicate 409、regenerate、BFF abort 不丢 finalize。

**不改 API** 即可先做 Phase 1（API 已在 V1 发 `sources`）。

### Phase 2 — 前端：结构化 UI

**文件**：`apps/web/components/chat/chat-message.tsx`、`apps/web/stores/chat-store.ts`、`apps/web/lib/chat-types.ts`

1. `useChat` / store 读取 data parts → `pendingSources` / `message.annotations`。
2. 助手气泡下方 **引用 chip 列表**（external_id、collection、score tooltip）。
3. 流式中：sources 先到 → 显示 skeleton/chips → 再收 token。
4. Markdown `## 参考来源` 可保留作 fallback，或 prompt 改为仅 structured（二选一，人审定）。

### Phase 3 — 持久化（推荐）

**文件**：Alembic migration、`apps/api/app/models/message.py`、message schemas、list API

1. `messages.metadata` JSONB：`{ "rag_sources": RagSourceItem[] }`。
2. `finalize_completion_stream` 写入（与 `completion_status` 同事务）。
3. `GET /conversations/{id}/messages` 返回 metadata；前端历史消息渲染 chips。

**回滚**：migration 可空列；旧消息 `metadata` null → 仅显示正文。

### Phase 4 — 测试与观测

- Harness：扩展 `test_rag_chat_contract.py` 或新增 `test_rag_chat_stream_contract.py`（直连 API 已有；加 BFF 需 Playwright 或 Next route handler 单测）。
- 可选：LangSmith span 标注 retrieve / sources / generate 耗时（对齐 EP04 Story 4.7 方向）。

---

## 5. 关键设计决策（待 follow-up 人审）

| 问题 | 选项 | 建议 |
|:-----|:-----|:-----|
| BFF 协议 | 继续 text/plain + 自定义前缀 vs AI SDK Data Stream | **Data Stream**（与 `useChat` 生态一致） |
| 历史消息引用 | 仅 Markdown vs DB metadata | **DB metadata** + UI chips |
| Prompt 是否还写 `## 参考来源` | 双写 vs 仅 structured | Phase 2 后可 **去掉 Markdown 脚注**，减 token |
| `done` 与 `sources` 重复 | 只发 `sources` vs 双发 | 保留双发：`sources` 早展示，`done` 绑定 id |
| 多实例 cancel | 现 Redis cancel | **不变**；data stream 不得破坏 drain |

---

## 6. 文件索引（升级时会动）

| 层 | 路径 |
|:---|:-----|
| API SSE | `apps/api/app/services/chat_service.py` |
| API 持久化 | `apps/api/app/services/chat_service.py` · `models/message.py` |
| BFF | `apps/web/app/api/chat/route.ts` |
| SSE 解析 | `apps/web/lib/sse-frames.ts` · `memoryos-upstream.ts` |
| 聊天 Hook | `apps/web/hooks/use-chat-session.ts` |
| UI | `apps/web/components/chat/chat-message.tsx` |
| Cancel 回归 | [chat-stream-cancel.md](./chat-stream-cancel.md) §4.3、§6 |
| OpenSpec（未来） | `openspec/changes/ep04-rag-chat-stream/` |

---

## 7. 变更记录

| 日期 | 说明 |
|:-----|:-----|
| 2026-06-08 | 初稿：`ep04-rag-chat` propose 时记录 BFF token-only 限制与 Data Stream 升级路线 |
