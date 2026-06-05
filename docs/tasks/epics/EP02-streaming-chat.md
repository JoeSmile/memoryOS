# EP02 — 流式对话与多轮会话

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 3 周 |
| **优先级** | P0 |
| **依赖** | EP01、EP03 |
| **状态** | 🟡 按 Program 7 Phase 推进 |
| **OpenSpec 总控** | [`ep02-program`](../../../openspec/changes/ep02-program/) — **7 Phase 全部完成前不启动 EP04+** |
| **子 change** | 见下表 |
| **学习路线** | [L02-streaming-langgraph.md](../learning/L02-streaming-langgraph.md) |
| **目标文档** | `docs/tech/langgraph-chat.md` |

---

## 七阶段交付顺序（OpenSpec）

| Phase | 内容 | OpenSpec / 产出 | 状态 |
|:-----:|:-----|:----------------|:-----|
| **1** | 数据层收尾 | [`ep03-db-optimize`](../../../openspec/changes/ep03-db-optimize/) | ⬜ |
| **2** | LangGraph 学习 | L02 §5 + `langgraph-chat.md` | ✅ |
| **3** | LangSmith 环境 | 并入 Phase 4（`.env.example`） | ✅ |
| **4** | 最小 LangGraph | [`ep02-langgraph`](../../../openspec/changes/archive/2026-06-03-ep02-langgraph/) | ✅ |
| **5** | SSE + Graph 上游 | [`ep02-chat-sse`](../../../openspec/changes/archive/2026-06-03-ep02-chat-sse/) 后端 | ✅ |
| **6** | 最小 `/chat` 冒烟 | [`ep02-chat-sse`](../../../openspec/changes/archive/2026-06-03-ep02-chat-sse/) 前端 + archive | ✅ |
| **7** | 完整 UI + Markdown | [`ep02-chat-ui`](../../../openspec/changes/ep02-chat-ui/) | ⬜ |

执行：`/work-next ep02-program` 或按 Phase 对子 change 说「继续实现」。  
人审：每个 change 的 `tasks.md` §0。

---

## Story 映射（Phase 完成后勾选）

## Story 2.1 聊天 UI

- [ ] 布局：侧栏会话列表 + 主聊天区 → **Phase 7**
- [ ] 消息气泡、输入框、Loading、自动滚动 → **Phase 7**
- [ ] 响应式基础适配 → **Phase 7**

## Story 2.2 Markdown 渲染

- [ ] `react-markdown` + 代码高亮 → **Phase 7**
- [ ] GFM → **Phase 7**
- [ ] 流式不完整 Markdown 边界处理 → **Phase 7**

## Story 2.3 SSE 后端

- [x] `POST /api/v1/chat/completions` SSE 契约 → **Phase 5**
- [x] 对接大模型流式（经 LangGraph）→ **Phase 4–5**
- [x] 客户端断开时取消上游 → **Phase 5**

## Story 2.4 前端流式

- [x] ReadableStream / fetch 流式客户端 → **Phase 6**
- [x] Token 实时渲染、`AbortController` → **Phase 6**
- [ ] 网络异常与重试提示 → **Phase 6–7**

## Story 2.5 会话数据

- [x] 会话 CRUD、历史消息加载 → **Phase 1 + 5–6**（列表仍 query `user_id`；消息列表已 JWT）
- [ ] 会话标题自动生成 → **Phase 7 或 follow-up**
- [ ] Zustand → **Phase 7**

## Story 2.6 LangGraph 对话编排（核心）

- [x] 废弃业务层裸调 OpenAI → **Phase 5**（`ep02-chat-sse` 接 `ChatGraphRunner`）
- [x] Chat State、节点、边 → **Phase 4** [`langgraph-chat.md`](../../tech/langgraph-chat.md)
- [ ] 条件分支（EP05 预留）→ 后续

## Story 2.7 LangSmith

- [x] 账号 / Project / API Key → `.env.example` + 本地 `.env`（不提交密钥）
- [x] 环境变量分 dev/prod → `LANGSMITH_PROJECT` 等见 `.env.example`
- [ ] trace 可查 → 本地开 tracing 后手工验证（`ep02-chat-sse` 后联调）

---

## 同步学习

- [ ] React 高复用组件封装 → Phase 7 前
- [ ] Zustand 实战 → Phase 7
- [x] SSE 原理与前后端联动 → Phase 5–6
- [ ] LangGraph：State、Node、Edge → **Phase 2–4**
- [ ] LangSmith 配置与排错 → **Phase 3–4**
- [ ] 多轮上下文拼接与 Prompt 基础 → Phase 4+
