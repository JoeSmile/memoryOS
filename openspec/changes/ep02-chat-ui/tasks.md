## 0. Human review（apply 前必过）

- [ ] **Tasks reviewed by human**

### Review checklist

- [ ] `ep02-chat-sse` 已 archive
- [ ] JWT 与 conversations 列表策略明确
- [ ] 依赖加入 `apps/web/package.json`

**Reviewer notes:**

---

## 1. Dependencies & layout

- [ ] 1.1 添加 zustand、react-markdown、remark-gfm、高亮库
  - 预计文件：1 · `apps/web/package.json`
  - **已提前接入（Phase 6+）：** `@tanstack/react-query`、`ai`、`@ai-sdk/react`

- [ ] 1.2 侧栏 + 主区布局骨架 `components/chat/*`
  - 预计文件：3 · 层：components、app/chat

## 2. Zustand & 会话列表

- [ ] 2.1 `useSessionStore` + 对接 `GET /conversations`
  - 预计文件：2 · stores、lib

- [ ] 2.2 `useChatStore` + send/abort 接 `sse-client`
  - 预计文件：2 · stores、hooks
  - **已部分实现：** `useChat` + `TextStreamChatTransport`（`/api/chat` BFF）；Zustand 仍待做

## 3. Markdown & polish

- [ ] 3.1 `MessageContent` Markdown + 流式边界
  - 预计文件：2 · components

- [ ] 3.2 滚底、Loading、空态；EP02 Story 2.1–2.2、2.5 勾选
  - 预计文件：2 · components、docs/epic

**前置：** `ep02-program` Phase 6 完成。
