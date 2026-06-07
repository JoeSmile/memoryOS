## Context

- `ep02-chat-dedup`（archived）已实现：`is_disconnected()` 轮询、`finalize_completion_stream` 落库 `interrupted`/`complete`、BFF TextStream、前端「已中断」UI。
- 现状：`ChatGraphRunner` 用 `astream_events` 抽 token，但 `call_model` 对真实 LLM 仍 `ainvoke` 非流式路径；断开时仅停 SSE 读端，**未** `aclose` 上游 HTTP。
- EP02 backlog C.1–C.10 定义本 change；与 dedup **独立 PR**。

## Goals / Non-Goals

**Goals:**

- 用户 Stop 后，尽最大努力停止 LLM 上游 token 生成与计费。
- HTTP abort 失效时，`POST .../cancel` 仍可设 Redis cancel 标记，多 worker 可协调。
- 保留 dedup 的 interrupted 落库与 UI（本 change 不删 partial 策略）。
- Harness 覆盖 disconnect + cancel-only；`pnpm test:api:harness` 全绿。

**Non-Goals:**

- 修改 `client_message_id` / regenerate 语义。
- 从 partial 内容续接 LLM context。
- 供应商侧 100% 停费保证（文档说明「best effort」）。

## Decisions

### D1: `stream_id` 下发时机

- **选择**：SSE 连接建立后**首帧** `{"event":"start","data":{"stream_id":"<uuid>"}}`（与 token 同 envelope）；可选响应头 `X-Stream-Id` 冗余。
- **理由**：BFF TextStream 可忽略非 token 事件；cancel API 尽早有目标。比仅 `done` 带出更早。
- **替代**：仅响应头 — BFF/浏览器 fetch 可读，但 AI SDK 路径需额外解析；首帧 SSE 与现有 parser 一致。

### D2: Redis cancel 标记

- **选择**：`memoryos:stream_cancel:{stream_id}`，TTL ≈ 流最大时长（120s）；`POST /cancel` 仅 `SET` 标记（幂等）。
- **选择**：活跃流注册 `memoryos:stream_active:{stream_id}` → `{conversation_id,user_id}` 用于归属校验。
- **理由**：多 worker / BFF abort 失效时仍可协调；与 `CompletionTurnLock` 键空间分离。
- **无 Redis**：进程内 `asyncio.Event` fallback（单 worker dev/harness）。

### D3: Cancel API 契约

- **选择**：`POST /api/v1/chat/completions/cancel` body `{ stream_id }`；JWT；校验 stream 归属当前 user；200 幂等（已 cancel 仍 200）。
- **错误**：未知 stream / 他人会话 → 404；未鉴权 → 401。

### D4: 上游断开实现

- **选择**：`call_model` 真流式（`astream` / `astream_events`）；`ChatGraphRunner.stream_tokens` 循环内双检：`is_disconnected()` OR `cancel_cache.is_cancelled(stream_id)`。
- **选择**：取消时 `task.cancel()` + `finally` 内 `await aclose()` / 关闭 LangChain 流。
- **理由**：主路径硬断开 HTTP；Redis 为兜底。

### D5: 前端混合 Stop

- **选择**：`stop()` 顺序：① `AbortController.abort()`（快）② fire-and-forget `POST /api/chat/cancel` with `stream_id`（稳）。
- **选择**：从 SSE `start` 事件或 BFF 透传头缓存 `streamIdRef`。
- **不改动**：dedup 的 `syncPersistedMessagesAfterAbort` / interrupted UI。

### D6: BFF 链路

- **选择**：`/api/chat/cancel` 代理 API cancel；`memoryosSseResponseToTextStream` 解析 `start` 存 ref（可选回调），`cancel()` 时 abort 上游 fetch **并** drain（保留 dedup 落库机会）。
- **理由**：补 `req.signal` 死角；与 dedup drain 行为兼容。

### D7: interrupted vs「已停止」文案

- **选择**：UI 仍用 dedup 的「已中断」+ `…`（`completion_status=interrupted`）；本 change 只保证上游更快停，不新增「继续生成」。
- **文档**：L02 §4 补充 AbortController + cancel API + 供应商计费边界。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| 供应商不支持 mid-stream cancel | 文档 best-effort；Harness mock 计数断言 |
| `stream_id` 泄漏 | 短 TTL + 归属校验 + JWT |
| 与 dedup finalize 竞态 | cancel 停上游；finalize 仍在 router `finally`（dedup 已实现） |
| change 过大 | tasks 按 C.1–C.10 拆条，每 task ≤3 文件 |

## Migration Plan

1. 部署 API（cancel 路由 + runner）→ 部署 Web（stop 双路径）。
2. 无 DB migration。
3. 回滚：关 cancel 路由；runner 回退；Redis 键 TTL 自然过期。

## Open Questions

- ~~是否改 interrupted 不落库~~ — **否**，沿用 dedup。
- Mock LLM harness 如何断言 upstream 停止 — 用 mock 计数 / 可注入 slow stream。
