# EP02 — 流式对话与多轮会话

| 属性              | 值                                                                                             |
| :---------------- | :--------------------------------------------------------------------------------------------- |
| **周期**          | 第 3 周                                                                                        |
| **优先级**        | P0                                                                                             |
| **依赖**          | EP01、EP03                                                                                     |
| **状态**          | 🟡 按 Program 7 Phase 推进                                                                     |
| **OpenSpec 总控** | [`ep02-program`](../../../openspec/changes/ep02-program/) — **7 Phase 全部完成前不启动 EP04+** |
| **子 change**     | 见下表                                                                                         |
| **学习路线**      | [L02-streaming-langgraph.md](../learning/L02-streaming-langgraph.md)                           |
| **目标文档**      | `docs/tech/langgraph-chat.md` · Stop/Cancel：[`chat-stream-cancel.md`](../../tech/chat-stream-cancel.md) |

---

## 七阶段交付顺序（OpenSpec）

| Phase | 内容                           | OpenSpec / 产出                                                                               | 状态                    |
| :---: | :----------------------------- | :-------------------------------------------------------------------------------------------- | :---------------------- |
| **1** | 数据层收尾                     | [`ep03-db-optimize`](../../../openspec/changes/ep03-db-optimize/)                             | ⬜                      |
| **2** | LangGraph 学习                 | L02 §5 + `langgraph-chat.md`                                                                  | ✅                      |
| **3** | LangSmith 环境                 | 并入 Phase 4（`.env.example`）                                                                | ✅                      |
| **4** | 最小 LangGraph                 | [`ep02-langgraph`](../../../openspec/changes/archive/2026-06-03-ep02-langgraph/)              | ✅                      |
| **5** | SSE + Graph 上游               | [`ep02-chat-sse`](../../../openspec/changes/archive/2026-06-03-ep02-chat-sse/) 后端           | ✅                      |
| **6** | 最小 `/chat` 冒烟              | [`ep02-chat-sse`](../../../openspec/changes/archive/2026-06-03-ep02-chat-sse/) 前端 + archive | ✅                      |
| **7** | 分析向聊天壳（单会话、无侧栏） | [`ep02-chat-ui`](../../../openspec/changes/ep02-chat-ui/)                                     | 🟡 实现完成，待 archive |

执行：`/work-next ep02-program` 或按 Phase 对子 change 说「继续实现」。  
人审：每个 change 的 `tasks.md` §0。

---

## Story 映射（Phase 完成后勾选）

## Story 2.1 聊天 UI

- [ ] ~~侧栏会话列表~~ → **移出 Phase 7**（世界杯向单会话；多会话侧栏见 EP10
      backlog）
- [x] 单会话主区：消息气泡、输入、Loading、自动滚动 → **Phase 7**
- [x] 消息管理钩子（regenerate）+ 上下文条数提示 → **Phase 7**
- [x] 响应式基础适配 → **Phase 7**（`max-w-3xl` 单栏）

## Story 2.2 Markdown 渲染

- [x] `react-markdown` + 代码高亮 → **Phase 7**
- [x] GFM → **Phase 7**
- [x] 流式不完整 Markdown 边界处理 → **Phase 7**

## Story 2.3 SSE 后端

- [x] `POST /api/v1/chat/completions` SSE 契约 → **Phase 5**
- [x] 对接大模型流式（经 LangGraph）→ **Phase 4–5**
- [x] 客户端断开时取消上游 → **Phase 5**

## Story 2.4 前端流式

- [x] ReadableStream / fetch 流式客户端 → **Phase 6**
- [x] Token 实时渲染、`AbortController` → **Phase 6**
- [x] 网络异常与重试提示 → **Phase 6–7**

## Story 2.5 会话数据

- [x] 会话 CRUD、历史消息加载 → **Phase 1 + 5–6**（列表仍 query
      `user_id`；消息列表已 JWT）
- [ ] 会话标题自动生成 → **Phase 7 或 follow-up**
- [x] Zustand（`useChatStore`，无 session 列表 store）→ **Phase 7**

## Story 2.6 LangGraph 对话编排（核心）

- [x] 废弃业务层裸调 OpenAI → **Phase 5**（`ep02-chat-sse` 接
      `ChatGraphRunner`）
- [x] Chat State、节点、边 → **Phase 4**
      [`langgraph-chat.md`](../../tech/langgraph-chat.md)
- [ ] 条件分支（EP05 预留）→ 后续

## Story 2.7 LangSmith

- [x] 账号 / Project / API Key → `.env.example` + 本地 `.env`（不提交密钥）
- [x] 环境变量分 dev/prod → `LANGSMITH_PROJECT` 等见 `.env.example`
- [x] trace 可查 → 本地开 tracing 后手工验证（`ep02-chat-sse` 后联调）

---

## 同步学习

- [x] React 高复用组件封装 → Phase 7 前
- [x] Zustand 实战 → Phase 7
- [x] SSE 原理与前后端联动 → Phase 5–6
- [x] LangGraph：State、Node、Edge → **Phase 2–4**
- [ ] LangSmith 配置与排错 → **Phase 3–4**
- [x] 多轮上下文拼接与 Prompt 基础 → Phase 4+

---

## Follow-up backlog（Phase 7 后，EP04 前可选）

两个**独立** OpenSpec change，勿与 `ep02-chat-dedup` / `ep02-chat-cancel`
混在一个 PR。

### `ep02-chat-dedup` — 发送幂等 + Regenerate 档 B（小）✅

|  #  | Task                                       | 层              | 说明                                          | 状态 |
| :-: | :----------------------------------------- | :-------------- | :-------------------------------------------- | :--- |
| D.1 | 前端 `isSending` 锁 + 提交后立即 disable   | Web             | 补 `isStreaming` 竞态窗口                     | [x]  |
| D.2 | 每条 user 消息 `client_message_id`（UUID） | Web → BFF → API | body 透传                                     | [x]  |
| D.3 | `messages.client_message_id` + 唯一索引    | API · Alembic   | `UNIQUE (conversation_id, client_message_id)` | [x]  |
| D.4 | `ChatService` 幂等：重复 id 不重复 insert  | API             | Harness 双 POST                               | [x]  |
| D.5 | `regenerate` flag（与幂等分离）            | API + Web       | 替换上一轮 assistant                          | [x]  |
| D.6 | L02 §1 + Harness 契约                      | Docs · tests    | 「防止重复提交」+ interrupted 落库            | [x]  |

**现状：** 已实现（change `ep02-chat-dedup`）；`pnpm test:api:harness` 含 duplicate / regenerate 契约。

### `ep02-chat-cancel` — 全链路停止 + 兜底 Cancel API（大，单独 change）

**目标：** 用户点停止后，尽最大努力停止 LLM 上游计费；HTTP
abort 失效时仍有兜底。

|  #   | Task                                                        | 层            | 说明                                                        |
| :--: | :---------------------------------------------------------- | :------------ | :---------------------------------------------------------- |
| C.1  | SSE `start` 事件或响应头下发 `stream_id`                    | API · BFF     | 流式一开始就可知 cancel 目标（现仅 `done` 带出）            | [x]  |
| C.2  | Redis `stream_cancel:{stream_id}` + 活跃流注册              | API · cache   | 多 worker 可协调；循环双检 `is_disconnected` OR cancel flag | [x]  |
| C.3  | `POST /api/v1/chat/completions/cancel`                      | API · Harness | JWT + 会话归属；幂等；仅设 cancel 标记                      | [x]  |
| C.4  | Runner `astream` + `finally: aclose()`；`call_model` 改流式 | API · graphs  | 主路径硬断开 LangChain/OpenAI HTTP                          | [x]  |
| C.5  | `ChatService`：`Task.cancel` / 断开时清理                   | API           | 不再只 `return` 不关闭生成器                                | [x]  |
| C.6  | 前端 `stop()`：Abort + fire-and-forget cancel API           | Web · BFF     | 混合：连接 abort（快）+ cancel API（稳）                    | [x]  |
| C.7  | BFF `ReadableStream.cancel` 联动 abort 上游 fetch           | Web           | 补 `req.signal` 链路死角                                    | [x]  |
| C.8  | UI「已停止」态；可选不落库 partial 策略文档化               | Web · docs    | 沿用 dedup「已中断」+ interrupted 落库（非删 partial）      | [x]  |
| C.9  | Harness：mid-stream disconnect + cancel-only                | tests         | cancel 停 token：单元测；API cancel 契约 Harness            | [x]  |
| C.10 | L02 §4 勾选 + 供应商计费边界说明                            | Docs          | AbortController + 上游取消（best-effort）                   | [x]  |
| C.11 | BFF drain 上游 + 停转发；`finalize` 竞态修复                | Web · API     | 见 [`chat-stream-cancel.md`](../../tech/chat-stream-cancel.md) §6.1–6.2 | [x]  |
| C.12 | cancel 带 `visible_content`；UI 乐观冻结                    | Web · API     | 停住所见 = 落盘内容                                       | [x]  |
| C.13 | 技术方案 + 踩坑文档                                         | Docs          | `docs/tech/chat-stream-cancel.md`                         | [x]  |

**现状：** change `ep02-chat-cancel` 已实现（含 C.11–C.12 follow-up）；`pnpm test:api:harness` 全绿。  
**计费：** Stop 后尽最大努力停上游 HTTP + Redis cancel 标记；供应商侧停费非 100% 保证。  
**详案：** [`docs/tech/chat-stream-cancel.md`](../../tech/chat-stream-cancel.md)
