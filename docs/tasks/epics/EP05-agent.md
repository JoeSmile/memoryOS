# EP05 — Unified ReAct Agent 工具调度

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 6 周 |
| **优先级** | P1 |
| **依赖** | EP02、EP04 |
| **学习路线** | [L04-agent.md](../learning/L04-agent.md) |
| **目标文档** | [`agent-langgraph.md`](../../tech/agent-langgraph.md) ✅ · [`langgraph-chat.md`](../../tech/langgraph-chat.md)（EP02 基础） |
| **OpenSpec** | [`2026-06-09-ep05-agent-tools`](../../../openspec/changes/archive/2026-06-09-ep05-agent-tools/) |

> **首 slice 定稿**：**Unified ReAct 单图** — 无用户 `mode`；`retrieve` 固定先跑；`tavily_search` 由模型 ReAct 触发（非硬路由）。原 Story 5.5「chat/agent 模式切换」**不在本 slice**。

---

## Story 5.1 工具 Schema ✅

- [x] 统一 Tool Schema（`ToolDefinition` + OpenAI function schema）
- [x] `ToolRegistry` + `ToolExecutor`
- [x] 首工具 `tavily_search`（无 Key mock · Harness 可跑）

## Story 5.2 LangGraph Unified ReAct ✅

- [x] **单图 ReAct**：`retrieve → call_model ↔ execute_tools`
- [x] `should_continue` 条件边 + `recursion_limit`
- [x] SSE 多轮 `tool_call` / `tool_result` + 流式 token
- [x] `metadata.tool_steps` 持久化 + 刷新 hydrate

## Story 5.3 内置工具（首 slice）✅

- [x] **网页搜索**：Tavily（`TAVILY_API_KEY`；mock fallback）
- [ ] 数据库只读查询、数据统计（后续 change 注册即可）
- [x] 知识库检索：**retrieve 节点**（非 tool；与 EP04 一致）

## Story 5.4 容错 ✅（首 slice）

- [x] 工具超时（`AGENT_TOOL_TIMEOUT_SECONDS`）
- [x] 畸形 tool_call → 错误 ToolMessage 回灌
- [x] Tavily 失败 → ToolMessage 错误，不抛 HTTP
- [x] `AGENT_TOOLS_ENABLED=false` 应急回滚 EP04 图

## Story 5.5 前端 ToolTimeline ✅

- [x] **无 mode toggle**（产品定稿）
- [x] ToolTimeline UI（dev 展开 summary · prod 折叠）
- [x] RAG citation chips 与 timeline 并存

## Story 5.6 LangSmith 📋

- [ ] 工具调用全流程 trace、失败 case 复盘（EP09+）

---

## 同步学习

- [x] Function Calling 协议（`ToolDefinition` / Registry）
- [x] LangGraph ReAct 架构（`should_continue` + tool loop）
- [x] 工具注册中心设计（加 tool 不改图）
- [x] 死循环与异常排查（recursion_limit + malformed call 单测）
- [ ] 复杂 Agent 节点解耦（parallel tools · 后续）

---

## Harness / 单测

| 层 | 文件 |
|:---|:-----|
| L1 Harness | `test_unified_react_contract.py` |
| Unit | `test_should_continue.py` · `test_execute_tools.py` · `test_tavily_tool.py` |
| Web | `test_sse_frames` · `test_memoryos_data_stream` · `test_chat_types_tool_steps` |

---

## 下一步（EP05 后）

1. **archive** `ep05-agent-tools` → 同步 `openspec/specs/`
2. 可选：DB 只读 tool、SearXNG、LangSmith L3 pass rate
3. EP09 Agent 稳定性统计
