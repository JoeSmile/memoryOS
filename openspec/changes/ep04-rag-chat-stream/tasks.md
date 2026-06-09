## 0. Human review（apply 前必过）

> propose 完成后 **必须停在这里**等人审；未勾选前 **禁止** 写业务代码。

- [x] **Tasks reviewed by human** — 人审通过后再 `/opsx:apply`、`/work-next` 或说「继续实现」

### Review checklist

- [x] BFF Data Stream 与 Stop/Cancel 回归（design D5 / chat-stream-cancel §6）
- [x] API metadata 持久化 + 列表 API 与前端 chips 成对
- [x] Harness 覆盖 design D6（metadata、sources SSE 已有路径）
- [x] 与 EP04 Story 4.6 structured chips 一致；每条 task ≤3 文件 / ~150 行
- [x] 溯源策略：**保留双写** — prompt 继续输出 Markdown `## 参考来源` + UI citation chips（本 change 不改 prompt）
- [x] Chip 交互：Popover 展示 preview，不跳转
- [x] 无命中：无空状态 chip；外部检索走 EP05 Tool

**Reviewer notes:**

- **依赖**：`ep04-rag-chat` ✅ archive；API 已发 `sources` / `done.data.sources`。
- **参考**：[`docs/tech/chat-rag-stream.md`](../../../docs/tech/chat-rag-stream.md)
- **人审已定**：**保留双写** — `rag_chat` prompt 仍要求 `## 参考来源`；chips 为增量 UI；旧消息无 metadata 时仍靠 Markdown fallback。
- **Chip 点击（已定）**：V1 **不跳转**；hover tooltip + **click 打开 Popover** 展示 `content_preview`（≤240 字）+ `external_id` / `collection` / score。全文需新 API，留 follow-up。
- **无命中（已定）**：**不做**空状态 chip；沿用 no-hit 助手文案；「去别的渠道查」留 **EP05 Agent Tool**（搜索 / 外部检索）。

---

## 1. SSE 解析

- [x] 1.1 `sse-frames.ts`：`extractSourcesItems`、`extractDonePayload`（含 `message_id`、`sources`）
  - 预计文件：1 · 层：`apps/web/lib`

## 2. BFF Data Stream

- [x] 2.1 `memoryos-upstream.ts`：`memoryosSseResponseToDataStream`（保留 `onStreamId` / `drainThenAbort` / `clientStopped`）
  - 预计文件：1 · 层：`apps/web/lib`

- [x] 2.2 `route.ts` + `use-chat-session.ts`：切换 Data Stream transport 与响应 MIME
  - 预计文件：2 · 层：BFF route + hook

## 3. API 持久化

- [x] 3.1 Alembic `messages.metadata` JSONB + `Message` model
  - 预计文件：2 · 层：alembic、models

- [x] 3.2 `MessageRead` schema + list API 返回 `metadata`
  - 预计文件：2 · 层：schemas、api（若 router 需改则 ≤3 含 router）

- [x] 3.3 `chat_service.py` finalize 写入 `metadata.rag_sources`（与 assistant row 同事务）
  - 预计文件：1 · 层：services

## 4. 前端 citation UI

- [x] 4.1 `chat-types.ts` + `chat-store.ts`：`RagSourceItem`、stream/history sources 状态
  - 预计文件：2 · 层：lib + store

- [x] 4.2 `chat-message.tsx`（+ `rag-source-chip` 或内联 Popover）：citation chips；与 Markdown `## 参考来源` **并存**；chip click → Popover（preview + 元数据，**不跳转**）
  - 预计文件：2 · 层：`components/chat`

## 5. Tests

- [x] 5.1 `tests/unit/test_memoryos_data_stream.ts`（或 `.tsx`）：converter mock SSE → data parts
  - 预计文件：1 · 层：`apps/web` unit

- [x] 5.2 扩展 `test_rag_chat_contract.py`：assert assistant message `metadata.rag_sources`
  - 预计文件：1 · 层：`tests/harness`（TDD 先写）

## 6. Closeout

- [ ] 6.1 `pnpm test:api:harness` + web unit 绿；更新 EP04-rag Story 4.6 + `chat-rag-stream.md` 状态
  - 预计文件：2 · 层：docs

- [ ] 6.2 archive change
  - 预计文件：0 · openspec archive
