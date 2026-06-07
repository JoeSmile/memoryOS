## Why

`ep02-chat-sse` 已交付最小 `/chat`（AI SDK + BFF + React Query）。产品方向调整为 **世界杯向分析 Web**（赛会 RAG、队伍/队员评分解读等，业务页在 **EP11**）：聊天壳子采用 **单会话深挖**，不做多会话侧栏，而强化 **会话内消息管理** 与 **上下文可见性**。对应 Program **Phase 7**；完成前不启动 EP04。

## What Changes

- **单会话主区**：保留 `?conversation_id=` 深链；无侧栏会话列表。
- **消息管理（MVP）**：稳定 `message.id`、为编辑/重发/重新生成预留 UI 钩子（完整交互可 EP11 迭代）。
- **上下文提示**：展示当前载入消息条数 / 简要「上下文窗口」说明（只读；裁剪策略在后端 follow-up）。
- **Markdown**：`react-markdown` + GFM；流式结束后渲染。
- **状态**：`useChatStore`（Zustand）整理 `useChat` + Query；**不**做 `useSessionStore` 列表。
- **复用**：BFF `/api/chat`、`TextStreamChatTransport`、React Query 历史拉取。

## Capabilities

### New Capabilities

- `chat-ui`: 单会话聊天壳、Markdown、消息管理钩子、上下文提示。

### Modified Capabilities

- （无）

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/web/components/chat/` | 消息区、Markdown、上下文条 |
| `apps/web/stores/` | `useChatStore`（无 session 列表 store） |
| `apps/web/package.json` | zustand、react-markdown 等 |
| `apps/web/app/chat/` | 从 `minimal-chat` 演进为分析向布局 |

**非本 change：** 世界杯球队榜/评分页（[`EP11` 设计 spec](../../../docs/superpowers/specs/2026-06-04-world-cup-sports-ai-design.md)）、LangGraph 上下文裁剪、RAG 溯源 UI。
