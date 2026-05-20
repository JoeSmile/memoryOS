# EP05 — LLM Agent 智能工具调度

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 6 周 |
| **优先级** | P1 |
| **依赖** | EP02、EP04 |
| **学习路线** | [L04-agent.md](../learning/L04-agent.md) |
| **目标文档** | `docs/tech/agent-langgraph.md` 📋 |

---

## Story 5.1 工具 Schema

- [ ] 统一 Tool Schema（name、description、parameters JSON Schema）
- [ ] `ToolRegistry` + `ToolExecutor`

## Story 5.2 LangGraph Agent 全链路

- [ ] **基于 LangGraph 重构**：思考 → 选工具 → 执行 → 观测 → 汇总
- [ ] ReAct 循环、最大迭代次数
- [ ] 流式推送思考过程（可选）

## Story 5.3 内置工具

- [ ] 网页搜索、数据库只读查询、知识库检索、数据统计（按需）

## Story 5.4 容错

- [ ] 超时、重试、降级、参数校验

## Story 5.5 模式切换

- [ ] `chat` / `agent` 模式 API + 前端切换
- [ ] 工具调用时间线 UI

## Story 5.6 LangSmith

- [ ] 工具调用全流程 trace、失败 case 复盘

---

## 同步学习

- [ ] Function Calling 协议（理解 / 落地）
- [ ] LangGraph ReAct 架构（理解 / 落地）
- [ ] 工具注册中心设计（理解 / 落地）
- [ ] 死循环与异常排查（理解）
- [ ] 复杂 Agent 节点解耦（理解 / 落地）
