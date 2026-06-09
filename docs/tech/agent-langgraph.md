# LangGraph Unified ReAct（EP05）

> **状态**：`ep05-agent-tools` 已落地 — 与 `apps/api/app/graphs/`、`apps/api/app/tools/` 对齐。  
> **学习**：[L04 §2 ReAct](../tasks/learning/L04-agent.md) · 前置 [langgraph-chat.md](./langgraph-chat.md)（EP02 单轮图）  
> **OpenSpec**：[`2026-06-09-ep05-agent-tools`](../../openspec/changes/archive/2026-06-09-ep05-agent-tools/)

---

## 1. 从 EP04 到 Unified ReAct

| 阶段 | 拓扑 | 用户可见 |
|:-----|:-----|:---------|
| EP04 | `retrieve → call_model → END` | RAG citation chips |
| EP05 | `retrieve → call_model ↔ execute_tools` | chips + **ToolTimeline** |

**产品决策（人审定稿）：**

- **无 `mode` 字段** — 用户不选 chat/agent；始终走同一图。
- **retrieve 固定先跑** — RAG 由图入口完成，不在 tool 里重复检索。
- **`rag_sufficient` 仅 prompt 提示** — 不用条件边强制 Tavily；模型 ReAct 自行决定是否调 `tavily_search`。
- **应急回滚** — `AGENT_TOOLS_ENABLED=false` 恢复 EP04 纯 RAG 图。

---

## 2. 在 MemoryOS 中的位置

```text
POST /api/v1/chat/completions
        │
        ▼
ChatService.stream_completion()
  · 累积 stream_state.tool_steps
  · finalize → metadata.tool_steps + rag_sources
        │
        ▼
ChatGraphRunner.stream_events()
  · sources? → tool_call/tool_result* → token*
        │
        ▼
compiled StateGraph (ReAct)
  retrieve_knowledge → call_model ↔ execute_tools
        │
        ▼
ToolRegistry + ToolExecutor
  · tavily_search（首 slice；无 Key 走 mock）
```

**分层**（与 EP02 相同）：

- `api/v1/chat.py` — 不 import LangGraph。
- `services/chat_service.py` — SSE 帧、落库、`metadata.tool_steps`。
- `graphs/` — 图、节点、runner；**无 SQL**。
- `tools/` — 注册表、执行器、builtin 工具。

---

## 3. ChatState 扩展

| 字段 | 说明 |
|:-----|:-----|
| `messages` | `add_messages` reducer；含 Human / AI / ToolMessage |
| `user_id` | JWT 用户，传给 ToolContext |
| `retrieved_chunks` | retrieve 节点写入；runner 发 `sources` SSE |
| `rag_sufficient` | prompt 提示用：`len(chunks)>0` 且 `max(score)≥阈值` |

实现：[`chat_state.py`](../../apps/api/app/graphs/chat_state.py)。

---

## 4. ReAct 图拓扑

```text
START
  → retrieve_knowledge     # 固定；写 chunks；SSE sources?
  → call_model             # bind_tools([tavily_search, …])
  → should_continue
       ├─ AIMessage.tool_calls 非空 → execute_tools ──┐
       │                                                │
       └─ 无 tool_calls → END ◄─────────────────────────┘
```

**条件边 `should_continue`**（[`execute_tools.py`](../../apps/api/app/graphs/nodes/execute_tools.py)）：

- 最后一条消息 **不是** `AIMessage` → `END`（含 ToolMessage 回灌后）
- `AIMessage.tool_calls` 非空 → `"execute_tools"`
- 否则 → `END`

**`recursion_limit`**：`AGENT_MAX_ITERATIONS`（默认 5），在 runner 传入 LangGraph config。

**编译入口**：[`chat_graph.py`](../../apps/api/app/graphs/chat_graph.py) — `build_chat_graph()` 按 `AGENT_TOOLS_ENABLED` 选 ReAct 或 EP04 图。

---

## 5. 节点职责

### 5.1 `retrieve_knowledge`

与 EP04 相同：向量检索 → `retrieved_chunks` → runner 格式化 `sources` SSE。

### 5.2 `call_model`

- `ChatOpenAI.bind_tools(registry.list_openai_schemas())`（有 Key 时）。
- Unified system prompt（[`unified_react.py`](../../apps/api/app/graphs/prompts/unified_react.py)）：RAG 够时优先用检索；弱 RAG 时指引调 Tavily。
- Mock 路径（无 Key）：[`mock_model.py`](../../apps/api/app/graphs/nodes/mock_model.py) — 弱 RAG 先 `tool_calls`，再 token。

### 5.3 `execute_tools`

1. 读 `AIMessage.tool_calls`。
2. `ToolExecutor.run(name, args, ToolContext)`。
3. 追加 `ToolMessage`（JSON：`success`、`summary`、`duration_ms`）。
4. 畸形 call（缺 name/id）→ 错误 ToolMessage，**不抛 HTTP**。

---

## 6. Tool 层

```text
apps/api/app/tools/
  definitions.py    # ToolDefinition
  registry.py     # 注册 + OpenAI schema
  executor.py       # 超时、校验、审计日志
  builtin/tavily_search.py
```

| 配置 | 默认 | 说明 |
|:-----|:-----|:-----|
| `TAVILY_API_KEY` | 空 | 空则 mock 搜索结果 |
| `AGENT_MAX_ITERATIONS` | 5 | LangGraph recursion_limit |
| `AGENT_TOOL_TIMEOUT_SECONDS` | 10 | Executor 单工具超时 |
| `AGENT_TOOLS_ENABLED` | true | false → EP04 图 |

**加新工具**：实现 handler → `registry.register()` → prompt 补一句；**图拓扑不变**。

---

## 7. SSE 与持久化

**事件顺序**：

```text
start → sources? → (tool_call → tool_result)* → token* → done
```

| 字段 | 时机 |
|:-----|:-----|
| `metadata.rag_sources` | finalize；与 EP04 相同 |
| `metadata.tool_steps` | finalize；每轮 `{ id, name, arguments, success, summary, duration_ms? }` |

Stop/interrupt：已 emit 的 tool 轮次仍写入 metadata（与 rag_sources 同策略）。

**前端**：BFF `data-tool-call` / `data-tool-result` → `ToolTimeline`；刷新靠 `toUIMessages` + store hydrate。见 [chat-rag-stream.md](./chat-rag-stream.md) 同级扩展。

---

## 8. 单测与 Harness 地图

| 文件 | 测什么 |
|:-----|:-------|
| `test_should_continue.py` | 条件边：空 messages、ToolMessage 后 END、有 tool_calls 路由 |
| `test_execute_tools.py` | 畸形 call、mock Tavily 执行 |
| `test_tavily_tool.py` | mock/空 query/registry |
| `test_unified_react_contract.py` | L1：RAG 够无 tool / 弱 RAG 有 Tavily + `metadata.tool_steps` |
| `test_chat_graph.py` | 整图 mock invoke 两场景 |

本地：

```bash
bash scripts/api.sh exec pytest tests/unit/test_should_continue.py tests/unit/test_execute_tools.py tests/unit/test_tavily_tool.py -q
pnpm test:api:harness   # test_unified_react_contract
```

---

## 9. 与 L04 学习清单对照

| L04 条目 | EP05 落地 |
|:---------|:----------|
| Function Calling schema | `ToolDefinition` + Registry |
| tool_calls / ToolMessage 回灌 | `execute_tools` 节点 |
| ReAct 条件边 | `should_continue` |
| recursion_limit | `AGENT_MAX_ITERATIONS` |
| 工具异常回灌 | Executor 失败 → ToolMessage JSON |
| 无限循环 | recursion_limit + Harness 断言 |

**尚未做（后续 change）**：parallel tools、DB 只读 tool、LangSmith L3 pass rate、LLM Judge。

---

## 10. 延伸阅读

- [langgraph-chat.md](./langgraph-chat.md) — EP02 StateGraph 基础
- [chat-rag-stream.md](./chat-rag-stream.md) — BFF Data Stream + metadata
- [L04-agent.md](../tasks/learning/L04-agent.md) — 面试题与踩坑表
