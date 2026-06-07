# 聊天流式停止（Stop / Cancel）技术方案

> **OpenSpec**：[`ep02-chat-cancel`](../../openspec/changes/ep02-chat-cancel/)  
> **学习**： [L02 §4](../tasks/learning/L02-streaming-langgraph.md)  
> **代码**：`apps/api/app/graphs/runner.py` · `services/chat_service.py` · `cache/stream_cancel_cache.py` · `apps/web/hooks/use-chat-session.ts` · `apps/web/lib/memoryos-upstream.ts`

---

## 1. 问题与目标

用户点击 **停止生成** 时，需要同时满足：

| 维度 | 目标 |
| :--- | :--- |
| **体验** | UI 尽快停住，不再继续出字 |
| **持久化** | 已显示的部分 assistant 落库为 `completion_status=interrupted`，刷新不丢 |
| **成本** | 尽最大努力停止 LangChain / 供应商上游 HTTP（**非 100% 停费保证**） |
| **多实例** | BFF `abort` 失效时，Redis cancel 标记仍可协调 |

与 [`ep02-chat-dedup`](../../openspec/changes/ep02-chat-dedup/) 的关系：**不删 partial**；interrupt 与 complete 共用 `finalize_completion_stream`，dedup 的 `client_message_id` 语义不变。

---

## 2. 端到端架构

```text
浏览器 stop()
  ├─ ① flushSync 冻结 assistant 可见文本（visible_content）
  ├─ ② POST /api/chat/cancel  { stream_id, visible_content? }  （并行、不等响应）
  └─ ③ useChat.stop() → AbortController abort BFF fetch

BFF  /api/chat
  ├─ req.signal.abort → drainThenAbort()（不再 enqueue 给浏览器；后台读上游 SSE）
  └─ 代理 completions SSE ↔ memoryosSseResponseToTextStream

API  POST /api/v1/chat/completions
  ├─ 首帧 SSE start + 响应头 X-Stream-Id
  ├─ StreamCancelCache 注册 stream_active:{id}
  ├─ ChatGraphRunner.stream_tokens 双检 disconnect | cancel（轮询 250ms）
  ├─ stream_completion_events → assistant_parts + token SSE
  └─ event_generator finally → finalize_completion_stream（必跑）

API  POST /api/v1/chat/completions/cancel
  └─ 归属校验 → SET stream_cancel:{id} + 可选 stream_cancel_visible:{id}
```

### 2.1 混合停止策略

| 路径 | 作用 | 速度 |
| :--- | :--- | :--- |
| **HTTP abort**（浏览器 → BFF → 可选上游 abort） | 尽快断开会话消费端 | 快 |
| **Cancel API**（Redis `stream_cancel:{stream_id}`） | 多 worker / abort 死角兜底 | 依赖 RTT |
| **Runner 轮询**（250ms） | 在 async for 循环内检测 disconnect / cancel | 最多 ~250ms 惯性 |

三者叠加为 **best-effort**；供应商侧是否立即停止计费取决于其 SDK / HTTP 实现。

### 2.2 关键数据结构

| 键 / 字段 | 说明 |
| :-------- | :--- |
| `memoryos:stream_active:{stream_id}` | `{conversation_id, user_id}`，cancel 归属校验 |
| `memoryos:stream_cancel:{stream_id}` | 取消标记，TTL 120s |
| `memoryos:stream_cancel_visible:{stream_id}` | 用户点击 Stop 时 UI 快照，finalize 截断用 |
| `CompletionStreamState.assistant_parts` | 服务端已 yield 的 token 列表 |
| `completion_status` | `interrupted`（cancel/disconnect）或 `complete` |

---

## 3. 落库规则（finalize）

`ChatService.finalize_completion_stream` **始终在** `chat.py` `event_generator` 的 `try` 末尾或 `finally` 中调用（dedup 起即如此），避免 BFF 先断导致未落库。

```python
# 优先级：visible_content（用户所见）⊆ 服务端已生成全文
content = _interrupted_content("".join(assistant_parts), visible_content)
completion_status = (
    COMPLETION_COMPLETE
    if stream_exhausted and not disconnected
    else COMPLETION_INTERRUPTED
)
```

| 场景 | 落库内容 | status |
| :--- | :--- | :--- |
| 用户 Stop 且传 `visible_content` | **屏幕上停住时的文本**（服务端更长则截断） | `interrupted` |
| 用户 Stop 未传 visible（旧客户端） | cancel 前服务端已 append 的全文 | `interrupted` |
| 正常流结束 | 全文 | `complete` |
| Tab 关闭 / disconnect | 已 append 部分 | `interrupted` |
| Stop 时无任何 token | 不落库（`assistant_parts` 空） | — |

---

## 4. 实现要点（按层）

### 4.1 API · Runner

- `call_model` 真流式：`astream` + `astream_events` 过滤 `on_chat_model_stream`。
- `stream_tokens`：`asyncio.wait(..., timeout=0.25)` 循环；每轮开头 `_should_stop(disconnect | cancel)`。
- 停止时 `pending.cancel()` + `agen.aclose()`，避免 LangChain HTTP 悬挂。
- **轮询间隔保持 250ms**（`_DISCONNECT_POLL_SECONDS`）：平衡 CPU 与 stop 惯性。

### 4.2 API · ChatService

- `stream_completion_events`：循环正常结束后若 `is_cancelled` → `disconnected=True`（**勿**标 `stream_exhausted`，否则误写 `complete`）。
- `cancel_stream`：先校验 `stream_active` 归属，再幂等 `set_cancelled`；**禁止**先 `is_cancelled` 短路跳过归属校验。

### 4.3 BFF

- `memoryosSseResponseToTextStream`：`clientStopped` 标志；abort 后 **立即停止 enqueue**，后台 `drainThenAbort` 读完上游以便 API `finalize`。
- `req.signal` 只触发 drain，**不**立刻 `upstreamAbort.abort()`（否则 finalize 来不及）。

### 4.4 Web

- `streamIdRef`：从 `X-Stream-Id` 或 SSE `start` 帧获取。
- `stop()`：`flushSync` 冻结 UI → fire-and-forget cancel（带 `visible_content`）→ `useChat.stop()`。
- `syncPersistedMessages({ retryUntilAssistant: true })`：Abort 后最多 15×200ms 重试，等待 interrupted 落库。

---

## 5. 测试策略

| 层级 | 覆盖 | 限制 |
| :--- | :--- | :--- |
| **Harness** | cancel API 401/404/200 幂等、归属、start 帧 | ASGI 单 transport **无法**并发「SSE 流 + cancel POST」做真 mid-stream 集成 |
| **Unit** | runner cancel 停 token、`ChatService` disconnect/cancel 落库、`visible_content` 截断 | mock slow stream + `asyncio.sleep` 模拟竞态 |
| **手工** | Stop → 刷新仍有 assistant；停住文本与 DB 一致 | 本地 `pnpm dev:stack` |

```bash
pnpm test:api:harness   # 含 test_chat_cancel_contract
bash scripts/api.sh exec pytest tests/unit/test_chat_service_interrupt.py tests/unit/test_chat_runner_stop.py -q
```

---

## 6. 实战踩坑（本 change 亲历）

### 6.1 停止后刷新 assistant 丢失

| 项 | 说明 |
| :--- | :--- |
| **现象** | 点 Stop 后刷新，最后一条 assistant 消失 |
| **根因 A** | BFF 将 `req.signal` 直接绑 `upstreamAbort.abort()`，API SSE 被硬掐，`finalize` 来不及 commit |
| **根因 B** | cancel 停止时 runner 正常 `return`，`stream_exhausted=True`，误落库为 `complete` 或竞态下未 persist |
| **修复** | BFF `drainThenAbort`（先读上游再 abort）；cancel 退出标 `disconnected` 而非 `stream_exhausted` |

### 6.2 Stop 后仍继续出字（体感滞后）

| 项 | 说明 |
| :--- | :--- |
| **现象** | 点击 Stop 后字符仍追加一段 |
| **根因** | 非单纯网络慢：cancel 异步 RTT + runner 250ms 轮询 + HTTP/SSE 管道缓冲 + BFF 为落库故意 drain 上游 |
| **修复** | UI `flushSync` 乐观冻结；BFF `clientStopped` 立即停止转发；cancel 与 abort 并行；落库用 `visible_content` 与 UI 对齐 |

### 6.3 落盘字数多于用户所见

| 项 | 说明 |
| :--- | :--- |
| **现象** | DB 里 assistant 比停住时更长 |
| **根因** | cancel 到达前 API 仍在 append；落盘取 `assistant_parts` 全文 |
| **修复** | cancel body 增加 `visible_content`；`finalize` 用 `_interrupted_content` 截断为用户快照 |

### 6.4 cancel 幂等短路跳过归属校验

| 项 | 说明 |
| :--- | :--- |
| **现象** | Code review 发现：`stream_active` 过期后 `stream_cancel` 仍在时，任意用户重放 cancel 可静默 200 |
| **根因** | `owner is None` 时若 `is_cancelled` 则直接 `return`，未校验归属 |
| **修复** | `owner is None` 一律 404；幂等 200 仅在 `get_active_owner` 成功且 `user_id` 匹配后 |

### 6.5 Harness 测不了真·流中 cancel

| 项 | 说明 |
| :--- | :--- |
| **现象** | 无法在同一 httpx client 上同时挂 SSE 与发 cancel |
| **规避** | mid-stream cancel 用 `ChatService` + `ChatGraphRunner` 单元测；Harness 只测 cancel API 契约 |

### 6.6 BFF pull 与 drain 共享 Reader 竞态

| 项 | 说明 |
| :--- | :--- |
| **现象** | abort 后偶发多吐几个 token 到浏览器 |
| **根因** | `pull()` 与 `drainThenAbort()` 同读 `body.getReader()` |
| **修复** | `clientStopped` 在 enqueue 前检查；abort 后只 drain 不转发 |

### 6.7 Runner 在 cancel 边界丢最后一个 pending token

| 项 | 说明 |
| :--- | :--- |
| **现象** | 循环开头见 cancel 即 `return`，已完成未 yield 的 pending chunk 不进 `assistant_parts` |
| **取舍** | 与 `visible_content` 方案一致时以 UI 快照为准；纯服务端路径可能少 1 chunk |
| **可选优化** | cancel 时先消费 pending 再 return（未做，当前依赖 visible 对齐） |

### 6.8 多 worker 与 Redis fallback

| 项 | 说明 |
| :--- | :--- |
| **现象** | 本地无 Redis 时 cancel 仅进程内有效 |
| **规避** | `StreamCancelCache` 双写 Redis + `_LOCAL_*`；生产应启 Redis |

---

## 7. 计费与产品边界（文档化）

- **MemoryOS 侧**：Stop 后停止读流、`aclose` 上游、Redis cancel 标记 — 已尽最大努力。
- **供应商侧**：OpenAI / 百炼等是否对已在途 token 计费，**无统一保证**；不承诺 100% 停费。
- **UI**：`interrupted` 显示「已中断」+ `…`；无「继续生成」（非本 change 范围）。

---

## 8. 演进与未做项

| 项 | 说明 |
| :--- | :--- |
| Runner 轮询改 event-driven | 可降惯性，当前固定 250ms |
| cancel 携带 `content_length` 替代全文 | 减 body 体积，等价截断 |
| Nginx `proxy_buffering off` | L02 §4 待勾选，防「假流式」 |
| 从 interrupted 续生成 | EP02 Non-Goal |

---

## 9. 相关文件速查

| 路径 | 职责 |
| :--- | :--- |
| `apps/api/app/graphs/runner.py` | 双检 disconnect/cancel，250ms 轮询，`aclose` |
| `apps/api/app/services/chat_service.py` | SSE 事件流、`finalize`、`visible_content` 截断 |
| `apps/api/app/cache/stream_cancel_cache.py` | active/cancel/visible 注册与 TTL |
| `apps/api/app/api/v1/chat.py` | completions SSE + cancel 路由 |
| `apps/web/hooks/use-chat-session.ts` | `stop()` 冻结 + cancel + abort |
| `apps/web/lib/memoryos-upstream.ts` | SSE→TextStream、drain、停转发 |
| `apps/web/app/api/chat/cancel/route.ts` | BFF cancel 代理 |

---

## 参考

- OpenSpec design：[`ep02-chat-cancel/design.md`](../../openspec/changes/ep02-chat-cancel/design.md)
- Dedup 中断落库：[`ep02-chat-dedup`](../../openspec/changes/ep02-chat-dedup/)
- LangGraph 流式总览：[`langgraph-chat.md`](./langgraph-chat.md) §6.4
