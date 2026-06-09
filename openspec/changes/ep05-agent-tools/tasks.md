## 0. Human review（apply 前必过）

> propose 完成后 **必须停在这里**等人审；未勾选前 **禁止** 写业务代码。

- [x] **Tasks reviewed by human** — 人审通过后再 `/opsx:apply`、`/work-next` 或说「继续实现」

### Review checklist

- [x] **Unified ReAct 单图**：retrieve → call_model ↔ execute_tools；**无** mode / **无** 规则强制 Tavily
- [x] RAG 够：多数 0 轮 tool；`sources` + chips 回归
- [x] RAG 弱：mock/真模型 **ReAct 调** `tavily_search`；tool SSE + timeline
- [x] **`metadata.tool_steps`**：finalize 写入 + 刷新后 timeline 从 metadata 恢复（mirror `rag_sources`）
- [x] Harness mock 两场景 + **`metadata.tool_steps` 断言**；Stop/Cancel 不变
- [x] 每条 task ≤3 文件 / ~150 行

**Reviewer notes（Unified ReAct，人审已定）：**

- **学习目标**：LangGraph 条件边、`bind_tools`、ToolMessage 回灌、`recursion_limit` — 见 `agent-langgraph.md`。
- **retrieve 固定先跑**；`rag_sufficient` 仅 prompt 提示，**不**硬路由 Tavily。
- **无 mode toggle**；`AGENT_TOOLS_ENABLED=false` 应急回滚 EP04 图。
- **tool_result.summary**：dev 展开；prod 折叠。
- **`metadata.tool_steps`（已定）**：与 `rag_sources` 同列；`finalize` 写入；`toUIMessages` + store hydrate；Stop 时已 emit 的 steps 仍保留。
- **风险接受**：弱 RAG 时模型可能不调 Tavily — Harness mock 覆盖；真环境靠 prompt + 后续 L3。

**数据流：**

```text
POST /chat/completions（无 mode）
  → retrieve_knowledge → sources?
  → call_model (bind_tools)
  → should_continue → execute_tools? → … → token* → done
  → BFF → chips? + ToolTimeline?（流式 store → 落库 metadata.tool_steps → 刷新 hydrate）
```

---

## 1. Tool 基础设施

- [x] 1.1 `ToolDefinition` + `ToolRegistry` + `ToolExecutor`
  - 预计文件：3 · 层：`apps/api/app/tools/`

- [x] 1.2 `tavily_search` + config（`TAVILY_API_KEY`、`AGENT_MAX_ITERATIONS`）；无 Key mock
  - 预计文件：2 · 层：`tools/builtin/` + `core/config.py`

## 2. Unified ReAct LangGraph

- [x] 2.1 扩展 `ChatState`（`rag_sufficient` 等）+ unified system prompt（RAG + tool 指引）
  - 预计文件：2 · 层：`graphs/chat_state.py` + `prompts/`

- [x] 2.2 `execute_tools` 节点 + `should_continue` 条件边；扩展 `chat_graph.py` ReAct 环
  - 预计文件：2 · 层：`graphs/nodes/` + `chat_graph.py`

- [x] 2.3 `call_model` 改 `bind_tools`；mock ReAct 两场景（够/弱 RAG）
  - 预计文件：2 · 层：`nodes/call_model.py` + `nodes/mock_model.py`

## 3. Runner & API

- [x] 3.1 `ChatGraphRunner` 多轮 `tool_call`/`tool_result` SSE + 流式 token
  - 预计文件：1 · 层：`graphs/runner.py`

- [x] 3.2 `chat_service.py`：`stream_state.tool_steps` 累积 + `finalize` 写 `metadata.tool_steps`；`AGENT_TOOLS_ENABLED` 回滚
  - 预计文件：2 · 层：`services/chat_service.py` + `schemas/message.py`（`ToolStepRead` 类型）

- [x] 3.3 Harness `test_unified_react_contract.py`（RAG 够无 tool / 弱 RAG 有 Tavily + **assert `metadata.tool_steps`**；TDD 先写）
  - 预计文件：1 · 层：`tests/harness`

## 4. BFF Data Stream

- [ ] 4.1 `sse-frames.ts` 解析 `tool_call` / `tool_result`
  - 预计文件：1 · 层：`apps/web/lib`

- [ ] 4.2 `memoryos-upstream.ts` → `data-tool-call` / `data-tool-result`
  - 预计文件：1 · 层：`apps/web/lib`

## 5. 前端（无 mode）

- [ ] 5.1 `chat-types.ts` + `chat-store.ts`：`ToolStepItem`、streaming/commit/hydrate（mirror `rag_sources`）
  - 预计文件：2 · 层：lib + store

- [ ] 5.2 `tool-timeline.tsx` + `chat-message.tsx` + `use-chat-session` hydrate（dev summary；刷新读 metadata）
  - 预计文件：3 · 层：`components/chat` + hook — **apply 时若超 3 文件拆 5.2a/5.2b**

## 6. Tests & docs

- [ ] 6.1 unit：`test_should_continue.py` + `test_execute_tools.py` + `test_tavily_tool.py`
  - 预计文件：3 · 层：`apps/api/tests/unit`（可拆 6.1a/6.1b 若超 3 文件 — apply 时拆 task）

- [ ] 6.2 `docs/tech/agent-langgraph.md`（ReAct 教材）+ EP05 epic；web converter 单测
  - 预计文件：2 · 层：docs + `apps/web/tests/unit`

- [ ] 6.3 archive change
  - 预计文件：0 · openspec archive
