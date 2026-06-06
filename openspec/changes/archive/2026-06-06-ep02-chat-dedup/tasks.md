## 0. Human review（apply 前必过）

- [x] **Tasks reviewed by human**

### Review checklist

- [x] `client_message_id` 幂等与 `regenerate` 行为与 design D2/D3/D6 一致
- [x] stop/abort 半截 assistant 落库 + UI 中断态（非正文拼 `…`）
- [x] Harness 覆盖 duplicate + regenerate；动 API 必 L1
- [x] 与 `ep02-chat-cancel` 无 scope 重叠
- [x] 每条 task ≤3 文件 / ~150 行

**Reviewer notes:**

---

## 1. Schema

- [x] 1.1 Alembic：`client_message_id` +
      `completion_status`（assistant：`complete`/`interrupted`）
  - 预计文件：1 · `apps/api/alembic/versions/`
  - 层：DB

- [x] 1.2 ORM `Message` + `MessageRead` 新字段
  - 预计文件：2 · `apps/api/app/models/message.py`、`schemas/message.py`
  - 层：models

## 2. API 契约与幂等

- [x] 2.1 `ChatCompletionRequest` 增加
      `client_message_id`、`regenerate`；Router 透传
  - 预计文件：2 · `schemas/message.py`、`api/v1/chat.py`
  - Harness：先扩 `test_chat_sse_contract.py`（duplicate / regenerate 红灯）

- [x] 2.2 `MessageRepository` 按 `client_message_id` 查询；`ChatService`
      幂等 user 插入 + 409 已完成 turn
  - 预计文件：2 ·
    `repositories/message_repository.py`、`services/chat_service.py`
  - Harness：双 POST 同 id 仅一条 user 行

## 3. 中断落库 & Regenerate

- [x] 3.1 断开时：有 partial 则写 `interrupted`
      assistant；D2 重试删 partial 再流
  - 预计文件：1 · `services/chat_service.py`
  - Harness：disconnect mock 后 DB 有 interrupted 行（unit：`test_chat_service_interrupt.py`）

- [x] 3.2 `regenerate=true`
      删最后 assistant（含 interrupted）、不插 user、再流式
  - 预计文件：1 · `services/chat_service.py`
  - Harness：regenerate 后 messages 条数不增 user

## 4. 前端

- [x] 4.1 `useChatSession`：`isSending` 锁 + 每发 `client_message_id`
  - 预计文件：1 · `hooks/use-chat-session.ts`
  - 层：Web

- [x] 4.2 BFF `/api/chat` 透传 `client_message_id`、`regenerate`
  - 预计文件：1 · `apps/web/app/api/chat/route.ts`
  - 层：BFF

- [x] 4.3 `regenerateLatest` 走 `regenerate` flag（非重发同文案 duplicate）
  - 预计文件：1 · `hooks/use-chat-session.ts`（可与 4.1 同 PR 若 ≤150 行）
  - 层：Web

- [x] 4.4 `ChatMessage`：`interrupted`
      展示省略号/「已中断」（**无「继续生成」按钮**）；刷新后与 DB 一致
  - 预计文件：2 · `chat-message.tsx`、`lib/chat-types.ts`
  - 层：Web

## 5. Verify & docs

- [x] 5.1 `pnpm test:api:harness` 全绿；`pnpm --filter @memoryos/web lint`
  - 预计文件：0 · 验证命令
  - 证据：`20 passed` harness；`eslint .` 0 error；`pnpm --filter @memoryos/web build` OK

- [x] 5.2 更新 L02 §1 + EP02 follow-up 勾选
  - 预计文件：2 ·
    `docs/tasks/learning/L02-streaming-langgraph.md`、`docs/tasks/epics/EP02-streaming-chat.md`

**前置：** `ep02-chat-ui` archive（或已合并 `feat/ep02-chat-ui`）。  
**勿与：** `ep02-chat-cancel` 同 PR。
