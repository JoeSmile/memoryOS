# L04 — LangGraph Agent（第 6 周）

**对应史诗**：EP05  
**前置**：L02 对话图、L03 知识库检索工具

---

## 1. Function Calling 基础

### 学什么

- [ ] 📖 OpenAI tools schema：`type: function`、`parameters` JSON Schema
- [ ] 📖 `tool_calls` 与 `tool` 角色消息回灌
- [ ] 📖 parallel tool calls：一次多个工具 vs 串行
- [ ] 📖 参数校验：必填、枚举、类型；失败如何反馈模型重试
- [ ] 🔧 统一 `ToolDefinition` + `ToolRegistry`

### 面试常问

- Function Calling 和 MCP 区别（能答一层）？
- 模型选错工具怎么办？如何写 tool description？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| description 模糊 | 乱调工具 | 写清「何时用/何时不用」+ 反例 |
| 未校验模型编的参数 | SQL 注入 / 越权 | schema 校验 + 白名单 |
| 工具返回超大 JSON | 撑爆 context | 截断 + 摘要再回灌 |

---

## 2. LangGraph ReAct 图

### 学什么

- [ ] 📖 模式：Reason → Act（tool）→ Observe → 循环 → Final
- [ ] 📖 节点：`agent`（绑 tools 的 LLM）、`tools`（执行器）、可选 `human`
- [ ] 📖 条件边：有 `tool_calls` 走 tools，否则 END
- [ ] 📖 `recursion_limit` / max iterations
- [ ] 📖 与 chat 图关系：共享 State 字段或子图 invoke
- [ ] 🔧 `apps/api/app/graphs/agent_graph.py`
- [ ] 🔧 `docs/tech/agent-langgraph.md`

### 面试常问

- 为什么 ReAct 比「一次 function call」更适合复杂任务？
- Agent 和 RAG chain 什么时候合并、什么时候分开？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 无限 tool 循环 | 费用爆炸 | 步数上限 + 重复调用检测 |
| 工具异常未回灌 | 模型胡编 | 错误信息作为 tool message 返回 |
| 同步阻塞工具 | 事件循环卡死 | httpx async / 线程池隔离 |

---

## 3. 内置工具实现

### 学什么

- [ ] 📖 **检索工具**：封装 L03 `retrieve_context`，只读
- [ ] 📖 **搜索工具**：Serper/Tavily API，限流
- [ ] 📖 **DB 工具**：只读 SQL、表白名单、行数上限
- [ ] 📖 工具日志：name、args、latency、success（审计）
- [ ] 🔧 至少 3 个工具 + 单元测试 mock LLM

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| DB 工具可写 | 数据被删 | 只读账号 + 语句拦截 |
| 搜索 API key 前端暴露 | 被盗刷 | 仅后端调用 |
| 检索工具未带 user_id | 越权看他人知识库 | 租户过滤 |

---

## 4. 容错：超时、重试、降级

### 学什么

- [ ] 📖 单工具超时（如 30s）
- [ ] 📖 指数退避重试（幂等工具才可重试）
- [ ] 📖 降级：搜索失败 → 仅知识库；全失败 → 友好提示
- [ ] 📖 用户侧：Agent 模式展示 tool 时间线（可选）

### 面试常问

- 如何设计工具调用的超时与重试策略？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 重试非幂等写操作 | 重复下单 | 写操作不重试 |
| 超时过短 | 正常搜索也失败 | 按工具类型配置 |
| 降级无日志 | 线上不知能力缩水 | 结构化 warn log |

---

## 5. chat / agent 模式切换

- [ ] 📖 API：`mode=chat|agent`；前端 Toggle
- [ ] 📖 UI：展示 tool 步骤 vs 纯流式文本
- [ ] 🔧 共用 session，消息表可增加 `metadata.tool_calls`

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| agent 流式与 chat SSE 格式不一 | 前端两套解析 | 统一 event schema |
| agent 费用高无提示 | 用户投诉 | 模式说明 + 用量展示（EP09） |

---

## 6. LangSmith 排错

- [ ] 📖 看 tool span：参数、返回、耗时
- [ ] 🔧 文档记录 2 个 failure case（死循环、错误参数）

## 阶段自测

- [ ] 白板 Agent 图 + 与 RAG 工具衔接点  
- [ ] 背诵「为何不裸 while 调 API」3 条理由  
- [ ] 演示：agent 模式查知识库 + 一次 web 搜索（mock 亦可）
