## Why

EP04 固定 RAG（retrieve → generate）无法让模型 **按需选工具**；无命中时只能兜底。EP05 学习目标是 **LangGraph ReAct 全链路**：用户 **不选模式**，统一图 **始终先 retrieve**，再进入 **Reason → Act（tool）→ Observe → 循环 → Answer**；模型在 RAG 不足时 **自行决定** 调用 `tavily_search`（及后续更多 tool），一次到位建立 Agent 基础设施。

## What Changes

- **Unified ReAct 图**：`retrieve_knowledge → call_model（bind tools）→ should_continue → execute_tools → 循环`；`recursion_limit` 防死循环；**无 `mode` 字段、无规则强制 Tavily**。
- **Tool 基础设施**：`ToolDefinition`、`ToolRegistry`、`ToolExecutor`；首工具 **`tavily_search`**（Tavily API；Key 仅后端；Harness mock）。
- **Prompt**：retrieve 后将 chunks 注入 system；指引「优先用检索上下文；不足时再调 `tavily_search`」；`state.rag_sufficient` 作提示字段（非硬路由）。
- **SSE**：`start → sources? → (tool_call/tool_result)* → token* → done`；支持 **多轮 tool**；RAG 有命中仍发 `sources` + citation chips。
- **BFF**：tool 事件 → Data Stream parts（与 `data-rag-sources` 并存）。
- **前端**：**无 mode toggle**；有 tool 调用时 **ToolTimeline**（多步）；dev 展开 `summary`；RAG chips 与 timeline 可并存。
- **持久化**：`finalize` 写入 `messages.metadata.tool_steps`；列表 API 返回；刷新后 ToolTimeline 从 metadata 恢复。
- **Harness**：`test_unified_react_contract.py` — mock LLM 两场景 + assert `metadata.tool_steps`。
- **文档**：`docs/tech/agent-langgraph.md`（ReAct 拓扑、学习要点、与 EP04 关系）；更新 EP05 Story 5.1–5.3、5.2、5.5（无模式切换）。

**Non-Goals（本 change 不做）：**

- 用户 `mode` toggle、规则 `route → 强制 Tavily`
- `knowledge_search` tool（retrieve 节点已注入 RAG context）
- parallel tool calls、human-in-the-loop
- DB 只读 / 统计 / SearXNG 自托管（后续 change 加 tool 即可）
- LangSmith L3 多轮 pass rate
- Playwright E2E

## Capabilities

### New Capabilities

- `agent-tools`: Tool Schema、Registry、Executor、`tavily_search`、ReAct `execute_tools` 契约

### Modified Capabilities

- `chat-sse`: Unified ReAct 多轮 `tool_call` / `tool_result`；RAG `sources` 不变
- `chat-ui`: 无模式切换；tool timeline + BFF tool parts
- `rag-chat`: retrieve 后 ReAct；`metadata.tool_steps` 持久化

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/app/tools/` | Registry、Executor、`tavily_search` |
| `apps/api/app/graphs/` | `execute_tools`、`should_continue`；ReAct 扩展 `chat_graph.py` |
| `apps/api/app/graphs/nodes/call_model.py` | bind_tools + unified system prompt |
| `apps/api/app/graphs/runner.py` | 多轮 tool SSE + 流式 token |
| `apps/api/app/services/chat_service.py` | `finalize` 写 `metadata.tool_steps` |
| `apps/api/app/schemas/message.py` | `MessageMetadataRead.tool_steps` 类型（可选） |
| `apps/api/app/core/config.py` | `TAVILY_API_KEY`、`AGENT_MAX_ITERATIONS` |
| `apps/api/tests/harness/` | `test_unified_react_contract.py` |
| `apps/web/` | sse-frames、upstream、tool-timeline |
| `docs/tech/` | `agent-langgraph.md`（ReAct 学习文档） |
| 依赖 | `tavily-python` 或 httpx |
