## 0. Human review（apply 前必过）

- [x] **Tasks reviewed by human**

### Review checklist

- [x] `ep02-program` Phase 1、`ep02-langgraph` Phase 4 计划已排期
- [x] Phase 5（后端）与 Phase 6（最小 UI）划分清晰
- [x] 不含侧栏/Markdown/Zustand（在 `ep02-chat-ui`）

**Reviewer notes:** 用户选择继续实现（task 1.1 起）。

---

**前置（必须）：** `ep02-langgraph` archive
✅（`archive/2026-06-03-ep02-langgraph`）  
**前置（推荐）：** `ep03-db-optimize` archive  
**编排：** [`ep02-program`](../ep02-program/tasks.md) Phase 5–6

---

## Phase 5 — 后端 SSE（先做）

### 1. Messages & harness (TDD)

- [x] 1.1 `MessageRepository` + harness `test_chat_sse_contract.py`（红灯）
  - 预计文件：2 · repositories、tests/harness

- [x] 1.2 `GET /conversations/{id}/messages` + ownership
  - 预计文件：2 · api/v1

### 2. ChatService + SSE route

- [x] 2.1 `ChatService` 接 `stream_tokens`（LangGraph）+ `StreamCache`
  - 预计文件：2 · services

- [x] 2.2 `POST /api/v1/chat/completions` SSE + router
  - 预计文件：2 · api/v1/chat.py

- [x] 2.3 断开取消 + harness 绿灯
  - 预计文件：2 · services、tests/harness

---

## Phase 6 — 最小前端（后端绿后）

- [x] 3.1 `lib/sse-client.ts`
  - 预计文件：1 · lib/

- [x] 3.2 `/chat` 最小流式 UI + 停止按钮
  - 预计文件：2 · app/chat、components

- [x] 3.3 历史消息 + 未登录跳转；docs；**archive 本 change**
  - 预计文件：2 · app/chat、docs

**下一步 change：** `ep02-chat-ui`（Program Phase 7）
