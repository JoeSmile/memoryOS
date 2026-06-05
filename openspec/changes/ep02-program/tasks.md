## 0. Human review（apply 前必过）

> 本 change 为 **总控编排**，不写业务代码。人审通过后按 Phase
> 1→7 执行子 change。

- [x] **Tasks reviewed by human** — 同意 7 Phase 顺序与 EP04+ 栅栏

### Review checklist

- [ ] Phase 6（最小 /chat）合并在 `ep02-chat-sse` 是否接受
- [ ] 子 change 列表完整：`ep03-db-optimize` → `ep02-langgraph` →
      `ep02-chat-sse` → `ep02-chat-ui`
- [ ] Phase 2 学习产出可验收

**Reviewer notes:**

---

## Phase 1 — 数据层收尾

**子 change：** [`ep03-db-optimize`](../ep03-db-optimize/)  
**Done：** archive + EP03 Story 3.5 勾选

- [ ] 1.1 完成并 archive `ep03-db-optimize`（`pnpm test:api:harness` 绿）

---

## Phase 2 — LangGraph 学习门禁

**产出：** 文档 + L02 理解（**无** `apps/api` 生产图代码）

- [x] 2.1 阅读并完成
      [L02 §5 LangGraph](../../../docs/tasks/learning/L02-streaming-langgraph.md)
      必读项勾选
- [x] 2.2 撰写 `docs/tech/langgraph-chat.md`
      初稿（State/Node/Edge/流式策略 ≥1 页）

---

## Phase 3 — LangSmith 环境

**并入：** `ep02-langgraph` task 1.1（本 Phase 以子 change 勾选为准）

- [x] 3.1 LangSmith dev Project + API Key 写入本地 `.env`（不提交密钥）
- [x] 3.2 `apps/api/.env.example` 含
      `LANGCHAIN_TRACING_V2`、`LANGCHAIN_API_KEY`、`LANGCHAIN_PROJECT` 说明

**Phase 3 Done 条件：** `ep02-langgraph` archive 且 3.1–3.2 已勾。

---

## Phase 4 — LangGraph 最小对话图

**子 change：** [`ep02-langgraph`](../archive/2026-06-03-ep02-langgraph/)  
**Done：** archive；Harness/unit 可流式出 token（mock 或 Key）

- [x] 4.1 完成并 archive `ep02-langgraph`

---

## Phase 5 — SSE 管道 + Graph 上游

**子 change：** [`ep02-chat-sse`](../ep02-chat-sse/)（后端 1–3 节）  
**Done：** `POST /chat/completions` SSE 由 **LangGraph**
驱动；`pnpm test:api:harness` 绿

- [x] 5.1 完成 `ep02-chat-sse` 后端 tasks（2.x–3.x）并 harness 绿

---

## Phase 6 — 最小聊天页（流式冒烟）

**子 change：** 仍属 [`ep02-chat-sse`](../ep02-chat-sse/)（前端 4.x）  
**Done：** `/chat` 可登录后发消息、看流式、停止；非侧栏完整 UI

- [x] 6.1 完成 `ep02-chat-sse` 前端 tasks（4.x）+ docs 5.1
- [x] 6.2 archive `ep02-chat-sse`

---

## Phase 7 — 分析向聊天壳（单会话 + Markdown）

**子 change：** [`ep02-chat-ui`](../ep02-chat-ui/)  
**产品向：** 世界杯分析 Web 复用；**无侧栏**；消息管理 + 上下文提示  
**Done：** archive；EP02 Story 2.1–2.2、2.5 勾选（侧栏项移出或标 N/A）

- [ ] 7.1 完成并 archive `ep02-chat-ui`

---

## 收尾 — archive 本 program

- [ ] P.1 更新 EP02 史诗状态为完成；archive `ep02-program`
- [ ] P.2 团队声明可启动 EP04 propose

**验证（Phase 1–7 后）：**

```bash
pnpm db:up && pnpm test:api:harness
pnpm --filter @memoryos/web build
# 浏览器：/chat 单会话流式 + Markdown + 消息管理/上下文提示（无侧栏）
```
