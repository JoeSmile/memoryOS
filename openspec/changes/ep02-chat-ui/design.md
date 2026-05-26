## Context

- 最小 `/chat` 与 `lib/sse-client.ts` 已存在（Phase 6）。
- conversations API 当前 `user_id` query；UI 阶段应用 JWT 用户 id 或等后端改造。

## Goals / Non-Goals

**Goals:**

- 侧栏：会话列表、新建会话、切换 `conversation_id`。
- 主区：消息列表 + 输入；流式消息更新 store。
- Markdown：助手消息渲染；代码块复制（可选）。
- 自动滚底策略（用户在底部才滚）。

**Non-Goals:**

- 虚拟列表（500+ 消息再上）。
- LangGraph 改动。
- 新 SSE 协议。

## Decisions

### D1: Zustand 拆分

- `useSessionStore`：列表、currentId、loading
- `useChatStore`：messages、streaming、send/abort

### D2: Markdown 流式

- 流式中：纯文本或简易 pre；`done` 后 Markdown 渲染（避免半截代码块炸裂）。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| 列表 API 未 JWT 化 | 临时用 `/me` 的 user id；follow-up issue |

## Migration Plan

1. `pnpm --filter @memoryos/web add zustand react-markdown …`
2. 重构 `/chat` 不破坏 Phase 6 冒烟路径（可保留 query 深链）。
