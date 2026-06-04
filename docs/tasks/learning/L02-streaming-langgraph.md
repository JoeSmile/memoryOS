# L02 — 流式对话 + LangGraph + LangSmith（第 3 周）

**对应史诗**：EP02  
**前置**：L01 完成 FastAPI 骨架 + JWT + 会话表

---

## 1. React 聊天 UI

### 学什么

- [ ] 📖 布局：侧栏（会话列表）+ 主区（消息流）+ 底部输入
- [ ] 📖 受控输入、Enter 发送、Shift+Enter 换行、发送中禁用
- [ ] 📖 列表虚拟滚动概念（消息 500+ 条时再上 `@tanstack/react-virtual`）
- [ ] 📖 自动滚底：`scrollIntoView` vs 判断用户是否在底部再滚
- [ ] 📖 空态 / Loading / Error 统一组件
- [ ] 🔧 `apps/web/components/chat/*`、`app/chat/page.tsx`

### 面试常问

- 流式输出时如何保持滚动体验？用户上滑看历史时要不要强制滚底？
- 如何防止重复提交同一条消息？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 在 Server Component 里做聊天 | 无法流式、无法输入 | 整页聊天区 `'use client'` |
| 每条消息一个 Context | 重渲染卡顿 | 列表项 memo + 稳定 key |
| `key={index}` | 流式更新乱序/闪烁 | 用 message `id` |
| 未处理竞态：慢请求覆盖新回复 | 显示错乱 | `AbortController` / 请求序号 |

---

## 2. react-markdown 与消息渲染

### 学什么

- [ ] 📖 `react-markdown` + `remark-gfm` + 代码高亮（shiki / rehype-highlight）
- [ ] 📖 流式未完成时的 Markdown 边界（可先纯文本后升级渲染）
- [ ] 📖 XSS：勿对助手内容 `dangerouslySetInnerHTML`；链接 `rel="noopener"`
- [ ] 🔧 `components/chat/MessageContent.tsx`

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 代码块在流式中断开 | 渲染炸裂 | 流式结束后再高亮，或节流渲染 |
| 复制代码按钮绑错层 | 点到整页 | 事件委托到 pre 级 |

---

## 3. Zustand 状态

### 学什么

- [ ] 📖 拆分 store：`useSessionStore` / `useChatStore` / `useUIStore`
- [ ] 📖 派生状态：当前会话 messages 用 selector 避免全量订阅
- [ ] 📖 异步 action：`sendMessage` 内聚 loading、error、abort
- [ ] 📖 与 URL 同步：当前 `sessionId` 可放 query（可选）
- [ ] 🔧 `apps/web/stores/useChatStore.ts`

### 面试常问

- Zustand 和 Redux / Context 选型？为什么 AI 聊天常用轻量 store？
- 流式 token 频繁更新如何减少渲染？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 整个 store 一次 set | 每条 token 全树重渲染 | 只更新当前 message 字段 |
| store 与 server 数据双源不一致 | 刷新丢消息 | 发送成功以 API 持久化为准再对齐 |

---

## 4. SSE 与 ReadableStream

### 学什么

- [ ] 📖 SSE 格式：`data: {...}\n\n`、`event:`、`id:`；与 WebSocket 对比
- [ ] 📖 FastAPI `StreamingResponse`、`text/event-stream`、心跳注释 `: ping\n\n`
- [ ] 📖 前端 `fetch` + `response.body.getReader()` 解码 UTF-8 分片
- [ ] 📖 `AbortController` 停止生成；断开时后端取消上游 LLM
- [ ] 📖 Nginx：`proxy_buffering off`、`proxy_read_timeout`
- [ ] 🔧 `POST /api/v1/chat/completions` + 前端 `lib/sse-client.ts`

### 面试常问

- SSE 和 WebSocket 怎么选？为什么很多 LLM 用 SSE？
- 客户端关闭 tab，服务端如何感知并停止计费？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 按 chunk 当完整 JSON 解析 | 随机 JSON 错 | 行缓冲拼 `data:` 行 |
| 忘记 `\n\n` 分隔 | 前端收不到事件 | 严格 SSE 格式 |
| Nginx 缓冲 | 「假流式」一次性出 | 关 buffering |
| 未鉴权 SSE | 被人刷接口 | 同 REST 鉴权中间件 |
| 错误走 200 + SSE error 事件 | 前端难区分 | 约定 error 事件或 HTTP 4xx |

---

## 5. LangGraph 对话编排

### 学什么

- [ ] 📖 **为何不用裸 while 调 OpenAI**：分支、重试、状态、可观测性失控
- [ ] 📖 `StateGraph`、`State`（TypedDict / Pydantic）、`Annotated` 累加 messages
- [ ] 📖 节点：入参 state → 返回 partial state；纯函数便于单测
- [ ] 📖 边：固定边 vs 条件边（`should_continue`）
- [ ] 📖 流式：`astream_events` / `stream_mode` 把 token 推到 SSE
- [ ] 📖 检查点（checkpoint）概念：为多轮、中断恢复铺垫
- [ ] 🔧 `apps/api/app/graphs/chat_graph.py`
- [ ] 🔧 `docs/tech/langgraph-chat.md`

### 面试常问

- LangGraph 和 LangChain Agent 区别？State 解决什么问题？
- 如何把 LangGraph 的一步步映射到前端 UI（thinking / tool / answer）？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 在节点里 mutating 全局 state | 并发请求串台 | 每请求独立 config / thread_id |
| 无最大步数 | 死循环烧 token | `recursion_limit` / 条件边 END |
| 流式与图节点阻塞混写 | 首 token 慢 | IO 放 async 节点 |
| 本地 graph 与生产 env 不一致 | 线上行为不同 | 配置化 model endpoint |

---

## 6. LangSmith

### 学什么

- [x] 📖 环境变量：`LANGCHAIN_TRACING_V2`、`LANGCHAIN_API_KEY`、`LANGCHAIN_PROJECT`
- [ ] 📖 Trace 结构：Run → 子 Run（LLM、Retriever、Tool）
- [ ] 📖 用 trace 看：延迟在 prompt 组装还是 model 还是网络
- [ ] 📖 数据集 / 回放（入门即可）
- [ ] 📖 与 **TruLens（§7）**
      分工：LangSmith 看 LangChain 生态 Run 树；TruLens 深挖 LangGraph 节点、`@task`、反馈评估
- [ ] 🔧 dev 项目与 prod 项目分离；`.env.example` 注明

### 面试常问

- 线上问题如何用 LangSmith 定位？举例一次「慢在检索还是生成」。

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 生产全量 trace | 额度爆 | 采样率 / 仅错误全量 |
| trace 含用户隐私 | 合规风险 | 脱敏后上报 |
| 未关 tracing 跑压测 | 费用惊人 | 压测环境单独 key |

---

## 7. TruLens（LangGraph 调试与评估）

> **用途**：EP02 起在本地/联调阶段用 **TruGraph**
> 看清图内每一步（节点、`@task`、工具），并预留 **Feedback**
> 做回答质量评估；生产主 trace 仍以 LangSmith（§6）为准。

### 学什么

- [ ] 📖 TruLens 定位：OTel 兼容 trace + 可选 Feedback（groundedness、相关性等）
- [ ] 📖 与 LangSmith：**互补** — LangSmith 看整条链路与线上；TruLens 看
      **GRAPH_NODE / GRAPH_TASK**、多 Agent 图内路径
- [ ] 📖 包：`trulens-apps-langgraph`；`TruGraph(graph, app_name=..., app_version=...)`
- [ ] 📖 用法：`with tru_recorder:` 或 `session.App(...)` 包住 `invoke` /
      `astream`
- [ ] 📖 自动 instrument：`@task`、LangChain 子调用无需手改节点代码
- [ ] 📖
      OTel 模式：`TRULENS_OTEL_TRACING=1`（与 Jaeger/Tempo 等栈互通，入门知即可）
- [ ] 📖 Dashboard / `TruSession` 查看 record：输入输出、节点耗时、异常栈
- [ ] 🔧 `apps/api/scripts/sandbox_trulens_langgraph.py`（最小图 + 一次 invoke）
- [ ] 🔧 `docs/tech/langgraph-chat.md` §6 记录「何时开 TruLens vs LangSmith」

### 面试常问

- LangGraph 调试时 LangSmith 不够用时，TruLens 多看到什么？（节点级、task 装饰器、反馈指标）
- Feedback function 和 trace 的关系？能否无标注先跑 trace 再补评估？

### 实战易踩坑

| 坑                             | 现象                     | 规避                                        |
| :----------------------------- | :----------------------- | :------------------------------------------ |
| 只开 LangSmith 不看图内节点    | 不知卡在哪条边/哪个 node | 联调时并行开 TruGraph 包一层 compile 后的图 |
| 忘记 `with tru_recorder`       | 无 record                | 脚本/单测固定 context manager 模式          |
| dev 全量 Feedback 调 Judge LLM | 慢、贵                   | 先 trace，稳定后再加 1–2 条核心 Feedback    |
| TruLens + LangSmith 双开未采样 | 本地磁盘/额度涨          | 本地全开；压测/生产 TruLens 仅抽样或关      |
| 图未 `compile()` 就 wrap       | instrument 失败          | 对 **compiled** graph 建 TruGraph           |

---

## 8. Prompt 与多轮上下文

### 学什么

- [ ] 📖 消息数组顺序：system → history → user（当前）
- [ ] 📖 system 人设、边界、拒答策略
- [ ] 📖 Token 粗算（tiktoken）；超预算裁剪策略（为 EP06 铺垫）
- [ ] 📖 空历史、超长历史、工具结果插入位置
- [ ] 🔧 `apps/api/app/prompts/chat.py`

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 把检索原文无上限拼进 prompt | 超 context、贵 | TopK + 字符上限 |
| system 可被用户消息覆盖 | 注入 | system 固定 + 输入过滤 |
| 多轮未持久化就依赖内存 | 刷新丢上下文 | 以 DB messages 为准 |

---

## 沙箱（先跑通再接入业务）

- [ ] 🔧 `apps/api/scripts/sandbox_langgraph_minimal.py`
- [ ] 🔧 `apps/api/scripts/sandbox_langsmith_trace.py`
- [ ] 🔧 `apps/api/scripts/sandbox_trulens_langgraph.py`（TruGraph +
      1 次 invoke，对照节点 span）

## 阶段自测

- [ ] 白板：用户输入 → LangGraph → SSE → Zustand → Markdown 渲染
- [ ] LangSmith 截 1 成功 + 1 失败 trace 写入 `docs/tech/langgraph-chat.md`
- [ ] TruLens：同一条对话在 Dashboard 能指出 **至少 2 个 graph 步骤**（如
      `call_model` → END）
- [ ] 能讲 LangSmith vs TruLens 分工 + 3 个 SSE/LangGraph 相关踩坑
