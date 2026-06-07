## 0. Human review（apply 前必过）

- [x] **Tasks reviewed by human**

### Review checklist

- [x] `stream_id` / cancel API / 上游 `aclose` 与 design D1–D6 一致
- [x] 与 `ep02-chat-dedup` interrupted 落库无冲突（不删 partial 策略）
- [x] Harness 覆盖 start + cancel + disconnect；动 API 必 L1
- [x] 前后端成对（cancel API ↔ BFF ↔ stop()）
- [x] 每条 task ≤3 文件 / ~150 行

**Reviewer notes:**

---

## 1. Cache & stream identity

- [x] 1.1 `StreamCancelCache`：`stream_cancel:{id}` + `stream_active:{id}` 注册/TTL
  - 预计文件：2 · `apps/api/app/cache/stream_cancel_cache.py`、`cache/keys.py`
  - 层：cache · 无 Redis 时进程内 fallback

- [x] 1.2 `CompletionStreamState` / SSE 首帧 `start` 带 `stream_id`
  - 预计文件：2 · `services/chat_service.py`、`api/v1/chat.py`
  - Harness：断言首事件含 `start`（可先红灯）

## 2. Cancel API

- [x] 2.1 `POST /api/v1/chat/completions/cancel` schema + router
  - 预计文件：2 · `schemas/message.py`（或 `chat_cancel.py`）、`api/v1/chat.py`
  - Harness：`tests/harness/test_chat_cancel_contract.py`（401/404/200 幂等）

- [x] 2.2 `ChatService.cancel_stream`：归属校验 + 设 Redis 标记
  - 预计文件：1 · `services/chat_service.py`
  - Harness：cancel-only 后 token 循环退出（mock 计数）

## 3. Runner 上游断开

- [x] 3.1 `call_model` 真流式（`astream`）；mock 保持可测
  - 预计文件：2 · `graphs/nodes/call_model.py`、`graphs/nodes/mock_model.py`
  - 层：graphs

- [x] 3.2 `ChatGraphRunner`：`aclose` / `finally`；循环双检 disconnect **或** cancel
  - 预计文件：1 · `graphs/runner.py`
  - 层：graphs

- [x] 3.3 `ChatService` token 循环接入 cancel 检查；断开时 `Task.cancel` 清理
  - 预计文件：1 · `services/chat_service.py`
  - Harness：mid-stream disconnect 无新 token（mock slow stream）

## 4. 前端 & BFF

- [x] 4.1 BFF `POST /api/chat/cancel` 代理 + `memoryos-upstream` 解析 `start` 存 `streamId`
  - 预计文件：2 · `apps/web/app/api/chat/cancel/route.ts`、`lib/memoryos-upstream.ts`
  - 层：BFF

- [x] 4.2 `useChatSession.stop()`：Abort + fire-and-forget cancel；保留 dedup sync
  - 预计文件：1 · `hooks/use-chat-session.ts`
  - 层：Web

- [x] 4.3 BFF `ReadableStream.cancel` 联动上游 abort（与 dedup drain 兼容）
  - 预计文件：1 · `lib/memoryos-upstream.ts`
  - 层：BFF

## 5. Verify & docs

- [x] 5.1 `pnpm test:api:harness` 全绿；`pnpm --filter @memoryos/web lint`
  - 预计文件：0 · 验证命令

- [x] 5.2 L02 §4 + EP02 `ep02-chat-cancel` 勾选；供应商计费边界说明
  - 预计文件：2 · `docs/tasks/learning/L02-streaming-langgraph.md`、`docs/tasks/epics/EP02-streaming-chat.md`

**前置：** `ep02-chat-dedup` 已 archive / 合并。  
**勿与：** `ep02-chat-dedup` 同 PR。
