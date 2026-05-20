# EP02 — 流式对话与多轮会话

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 3 周 |
| **优先级** | P0 |
| **依赖** | EP01、EP03 |
| **学习路线** | [L02-streaming-langgraph.md](../learning/L02-streaming-langgraph.md) |
| **目标文档** | `docs/tech/langgraph-chat.md` 📋 |

---

## Story 2.1 聊天 UI

- [ ] 布局：侧栏会话列表 + 主聊天区
- [ ] 消息气泡、输入框、Loading、自动滚动
- [ ] 响应式基础适配

## Story 2.2 Markdown 渲染

- [ ] `react-markdown` + 代码高亮（shiki / rehype-highlight）
- [ ] GFM：表格、引用、任务列表
- [ ] 流式不完整 Markdown 边界处理

## Story 2.3 SSE 后端

- [ ] `POST /api/v1/chat/completions` SSE 契约
- [ ] 对接大模型流式（经 LangGraph，见 2.6）
- [ ] 客户端断开时取消上游

## Story 2.4 前端流式

- [ ] ReadableStream / fetch 流式客户端
- [ ] Token 实时渲染、`AbortController` 停止生成
- [ ] 网络异常与重试提示

## Story 2.5 会话数据

- [ ] 会话 CRUD、历史消息加载
- [ ] 会话标题自动生成
- [ ] Zustand：`sessions`、`messages`、`loading`、`error`

## Story 2.6 LangGraph 对话编排（核心）

- [ ] **废弃**业务层裸调 OpenAI API
- [ ] 定义 Chat State（messages、user_id、model…）
- [ ] 节点：预处理 → 调模型（流式）→ 后处理
- [ ] Edge 与条件分支（为 EP05 预留）

## Story 2.7 LangSmith

- [ ] 账号 / Project / API Key 配置
- [ ] 环境变量分 dev/prod
- [ ] 对话链路 trace 可查、耗时可分析

---

## 同步学习

- [ ] React 高复用组件封装（理解 / 落地）
- [ ] Zustand 实战（理解 / 落地）
- [ ] SSE 原理与前后端联动（理解 / 落地）
- [ ] LangGraph：State、Node、Edge（理解 / 落地）
- [ ] LangSmith 配置与排错（理解 / 落地）
- [ ] 多轮上下文拼接与 Prompt 基础（理解 / 落地）
