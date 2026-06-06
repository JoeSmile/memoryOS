## Context

- Phase 7 `ep02-chat-ui` 已交付单会话壳；`POST /chat/completions` 每次请求无条件 `messages.create(user)`。
- Regenerate MVP：`sendMessage` 重发最后 user 文案 → DB/UI duplicate turn。
- EP02 follow-up 将本能力与 `ep02-chat-cancel`（大）**拆分**，本 change 保持小步、可单 PR 完成。

## Goals / Non-Goals

**Goals:**

- 正常发送：同 `client_message_id` 不重复插入 user 行（网络重试 / 双点兜底）。
- 前端：`isSending` 消除 `isStreaming` 切换前的竞态窗口。
- Regenerate：`regenerate=true` 不新增 user 行；替换上一轮 assistant（档 B）。
- Harness 覆盖幂等与 regenerate；`pnpm test:api:harness` 绿。

**Non-Goals:**

- LLM 上游 cancel、Cancel API（`ep02-chat-cancel`）。
- 编辑 user 消息后重发 UI。
- 无 `client_message_id` 的旧客户端：保持兼容（无键则行为与现网相同，仍可能 duplicate）。

## Decisions

### D1: `client_message_id` 放在 user 消息行

- **选择**：可选 UUID 列 `messages.client_message_id`；`UNIQUE (conversation_id, client_message_id) WHERE client_message_id IS NOT NULL`（PostgreSQL partial unique 或等价）。
- **理由**：幂等锚定在持久化层；assistant 仍由服务端生成 id。
- **替代**：仅 Redis 去重 TTL — 重启丢失，不采纳。

### D2: 重复 `client_message_id` 的行为

- **选择**：若 user 行已存在且同 turn 已有 **`completion_status=complete` 的 assistant** → **409** `duplicate_message`，不再开 SSE。
- 若 **无 assistant**，或仅有 **`interrupted` 半截 assistant**（见 D6）→ 复用 user 行；删除旧 partial（若有）后重新流式。
- **理由**：兼顾重试、stop/关页留痕与续写。

### D6: Stop / abort / 关页 — 半截 assistant 落库

- **选择**：`is_disconnected()`（含 stop→HTTP abort、关页）时，若已缓冲 token 非空 → 写入 assistant 行，`content` 为已生成正文（**不**在正文尾拼 `…`，避免破坏 Markdown/代码块）；`completion_status=interrupted`。
- **UI**：根据 `completion_status` 在气泡末展示省略号或「生成已中断」样式（纯展示层）。
- **空缓冲**（刚发就停）→ 仍不写 assistant，与现网一致。
- **与 dedup**：interrupted 视为「未完成 turn」，同 `client_message_id` 可重试覆盖；`regenerate` 可删 interrupted 最后一条 assistant 再生成。
- **Non-Goal**：从 partial 内容续接 LLM context（下一条仍按全量 history）；真停上游计费见 `ep02-chat-cancel`。

### D3: `regenerate` 与幂等分离

- **选择**：`regenerate: bool` 默认 `false`；为 `true` 时 **不** 创建 user 行，删除会话中 **最后一条 assistant**（若存在），再流式生成新 assistant。
- **理由**：产品语义是「重写回答」，不是「再发一条相同 user」。

### D4: 前端生成 id 的时机

- **选择**：`handleSubmit` / regenerate 分支在 `sendMessage` 前 `crypto.randomUUID()`；regenerate **不传** 新 `client_message_id`（或传新 id 仅用于 assistant 关联 — 本 change 简化为 regenerate 不走 client id）。
- **BFF**：`/api/chat` 从 AI SDK body 取出并转发。

### D5: `isSending` 本地锁

- **选择**：`useRef` 或 store 字段，`prepareSend` 后置 `true`，`onFinish`/`onError` 置 `false`；与 `isStreaming` 双检。
- **理由**：纯 UX 层，不替代 D2。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| 409 与前端重试逻辑冲突 | `apiFetch` 对 `duplicate_message` 视为成功并 refetch messages |
| regenerate 删 assistant 误删 | 仅删 **最后一条** 且 role=assistant；Harness 断言 |
| migration 在线库 | 新列 nullable；旧消息 `client_message_id` NULL |
| 无 client_message_id 旧路径 | 文档标明兼容；新前端始终带 id |

## Migration Plan

1. Alembic upgrade：`client_message_id` nullable UUID + unique index。
2. 部署 API → 部署 Web（开始带 id）。
3. 回滚：drop index + column（仅无依赖数据时）。

## Open Questions

- ~~流中断后「继续生成」按钮~~ — **MVP 不做**；仅展示 `interrupted` 态（省略号/「已中断」）。用户可用 **重新生成** 或 **重新发送**（新 `client_message_id`）收尾。
