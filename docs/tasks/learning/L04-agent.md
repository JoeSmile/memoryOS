# L04 — LangGraph Agent（第 6 周）

**对应史诗**：EP05

---

## 1. Function Calling

- [ ] 📖 OpenAI tools 格式、parallel tool calls
- [ ] 📖 参数 JSON Schema 校验
- [ ] 🔧 落地：统一 Tool Schema + 注册表

## 2. LangGraph ReAct

- [ ] 📖 `tools` 节点 + `agent` 节点 + 条件边
- [ ] 📖 最大步数、终止条件
- [ ] 🔧 落地：`apps/api/app/graphs/agent_graph.py`
- [ ] 🔧 落地：`docs/tech/agent-langgraph.md`

## 3. 工具中心

- [ ] 📖 工具描述质量对选型影响
- [ ] 🔧 落地：search / db / retrieval 至少 3 个工具

## 4. 排错

- [ ] 📖 死循环、错误参数、超时
- [ ] 🔧 落地：LangSmith 中 2 个 failure case 分析笔记

## 5. 架构

- [ ] 📖 节点解耦：规划 / 执行 / 汇总分离
- [ ] 🔧 落地：chat 模式与 agent 模式共用 State 基础字段

---

## 自测

- [ ] 能白板画出 Agent 图：入口 → LLM → 工具? → LLM → END  
- [ ] 能解释为何不裸写 while 循环调 API
