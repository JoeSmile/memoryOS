## 0. Human review（apply 前必过）

- [x] **Tasks reviewed by human**

### Review checklist

- [x] `ep02-chat-sse` 已 archive
- [x] 产品方向：世界杯向 **单会话**（无侧栏）；业务 UI 在 EP11
- [x] 消息管理 MVP 范围（regenerate stub / 编辑重发）可接受
- [x] 上下文提示仅 UI 展示、后端裁剪不在本 change
- [x] 依赖加入 `apps/web/package.json`

**Reviewer notes:** 用户确认按世界杯向产品调整 Phase
7：去掉侧栏，聚焦会话内消息管理与上下文可见性。

---

## 1. Dependencies & 单会话布局

- [x] 1.1 添加 zustand、react-markdown、remark-gfm、代码高亮库
  - 预计文件：1 · `apps/web/package.json`
  - **已接入：** `@tanstack/react-query`、`ai`、`@ai-sdk/react`

- [x] 1.2 单会话主区布局 `components/chat/*`（无侧栏）
  - 预计文件：3 · components、app/chat

## 2. 状态 & 消息管理

- [x] 2.1 `useChatStore`：整理 `useChat` +
      Query 同步（替代 minimal-chat 内联状态）
  - 预计文件：2 · stores、hooks

- [x] 2.2 消息管理 MVP：`message.id` 稳定、助手「重新生成」、上下文条数提示
  - 预计文件：2 · components/chat

- [x] 2.3 恢复最近会话 +「新建分析」（无侧栏）
  - 预计文件：4 · `GET /conversations/me`、hooks、chat-header
  - `/chat` 无 id → 拉最近 `updated_at` 会话；Header 显式新建

## 3. Markdown & polish

- [x] 3.1 `MessageContent` Markdown + 流式边界（done 后 GFM）
  - 预计文件：2 · components

- [x] 3.2 滚底、Loading、空态、错误态；更新 EP02 epic / docs
  - 预计文件：2 · components、docs

- [x] 3.3 Web Vitals 本地监控（`useReportWebVitals` dev 控制台 +
      `pnpm lighthouse:chat`）
  - 预计文件：3 ·
    `components/web-vitals-reporter.tsx`、`providers.tsx`、`package.json`
  - **Non-Goal：** 生产埋点 / Sentry（EP08）

**前置：** `ep02-program` Phase 6 完成。  
**下一步史诗：** EP11 世界杯业务页复用本聊天壳（独立 change）。
