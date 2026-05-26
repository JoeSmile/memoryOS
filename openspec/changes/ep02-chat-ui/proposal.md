## Why

`ep02-chat-sse` 交付最小 `/chat` 冒烟后，需要 EP02 完整体验：**侧栏会话列表**、**Markdown 消息**、**Zustand** 状态。对应 Program **Phase 7**；完成前不启动 EP04。

## What Changes

- 布局：`app/chat` 侧栏 + 主区（复用 SSE client）。
- `react-markdown` + GFM + 代码高亮；流式结束后再高亮（或节流）。
- Zustand：`useSessionStore` / `useChatStore`；与 API 持久化对齐。
- 会话列表对接 `GET /conversations`（JWT 绑定 follow-up 可同期）。
- **依赖**：`ep02-chat-sse` 已 archive。

## Capabilities

### New Capabilities

- `chat-ui`: 聊天布局、Markdown、客户端状态。

### Modified Capabilities

- （无）

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/web/components/chat/` | 新组件 |
| `apps/web/stores/` | Zustand |
| `apps/web/package.json` | 新依赖 |
| `apps/web/app/chat/` | 布局重构 |
