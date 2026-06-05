## Context

- Phase 6：`/chat` + `/api/chat` BFF + `useChat` + React Query 已上线。
- 产品：**世界杯向**单任务分析（一场对话里追问球队/队员/数据解读），非通用多会话收件箱。
- 后端：`GET /conversations/{id}/messages` 已 JWT；列表 API 仍 query `user_id`（本 change **不**做侧栏列表）。

## Goals / Non-Goals

**Goals:**

- 单会话全宽主区：消息列表 + 输入 + 停止；保留登录与 `conversation_id` 路由。
- **消息管理**：每条消息 `key={id}`；助手消息支持「重新生成」入口（MVP 可仅 UI + 接现有 `sendMessage`）；用户消息「编辑后重发」为 stub 或最小实现。
- **上下文可见性**：顶部或输入区旁展示「已载入 N 条消息」及简短说明（完整 token 预算 / 裁剪在 EP05、EP11 图节点）。
- **Markdown**：流式中纯文本；`done` 后 GFM + 代码高亮。
- **Zustand**：`useChatStore` 统一 streaming / messages 与 API 同步策略。
- 自动滚底：用户在底部时才滚。
- **Web Vitals（本地）**：development 下仅对 `needs-improvement`/`poor` 告警（终端 + 页角小条，不阻断）；可选 `NEXT_PUBLIC_WEB_VITALS_VERBOSE=1` 打全量；`pnpm lighthouse:chat` 对 `/chat` 出性能报告。

**Non-Goals:**

- 侧栏、多会话切换、`useSessionStore`、`GET /conversations` 列表 UI。
- 世界杯业务页面（球队榜、战力分卡片、RAG 文档上传）— **EP11**。
- LangGraph 图改动、SSE 协议变更、服务端 context 裁剪算法。
- 虚拟列表（消息 500+ 再上）。

## Decisions

### D1: 单会话而非侧栏

- **选择**：一个 `conversation_id` 对应一次分析会话；新建会话仍可通过无 query 时 `POST /conversations`（与 Phase 6 相同），但 **不**展示历史会话列表。
- **理由**：世界杯场景是「进入分析 → 连续追问」，不是邮件式多线程收件箱。
- **EP11**：业务路由（如 `/sports/{tournamentId}/teams/{id}`）可带 `?conversation_id=` 跳入同一壳子。

### D2: Zustand 只保留 `useChatStore`

- messages、streaming、error、与 `useChat` / Query invalidate 协同。
- **不**引入 `useSessionStore`。

### D3: 消息管理与上下文分工

| 层 | 职责 |
|:---|:-----|
| **UI（本 change）** | 展示消息、regenerate 按钮、上下文条数提示 |
| **API/Graph（后续）** | 发送前裁剪 history、RAG 注入、记忆写入 |

### D4: Markdown 流式边界

- 流式中：`pre` / 纯文本；`status === 'ready'` 且该条为完成后 → `MessageContent` Markdown。

### D5: 延续 AI SDK + BFF

- 不回到直连 `sse-client`；`lib/sse-client.ts` 保留作测试/备用。

### D6: Web Vitals 本地优先（异常告警）

- **选择**：`useReportWebVitals` 按 Google `rating` 过滤；异常时仅 `console.warn` + 右下角 12s 角标（**不发 HTTP**；`/api/dev/vitals` 仅保留 204 stub 兼容旧 bundle）；全量日志用 env 开关。
- **理由**：开发时视线在终端/编辑器，不必盯 Console；角标作备用且不 modal；生产上报留 EP08。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| 无侧栏切换会话 | 深链 `conversation_id` + 新建会话 URL 跳转 |
| regenerate 需后端支持 | MVP 仅重发最后 user 消息或 duplicate 最后 turn |
| 上下文提示仅为展示 | 文案标明「完整裁剪在后端」避免用户误解 |

## Migration Plan

1. `pnpm --filter @memoryos/web add zustand react-markdown remark-gfm`（及高亮库）。
2. 从 `minimal-chat.tsx` 拆出 `components/chat/*`，保留 Phase 6 冒烟路径可测。
3. EP11 复用本壳子，不换 SSE 栈。
