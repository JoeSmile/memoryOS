## Context

- **现状**：`retrieve_knowledge → call_model → END`；BFF 已支持 `sources` + citation chips。
- **产品 + 学习目标（人审）**：**Unified ReAct 一步到位** — 用户无 mode；学 LangGraph 条件边、tool 循环、ToolMessage 回灌。
- **约束**：Stop/Cancel 不变；Harness 无 `OPENAI_API_KEY` / `TAVILY_API_KEY` 可跑 mock ReAct。
- **参考**：[L04-agent.md](../../../docs/tasks/learning/L04-agent.md) §2 ReAct、[langgraph-chat.md](../../../docs/tech/langgraph-chat.md)。

## Goals / Non-Goals

**Goals:**

- 单图 Unified ReAct：`retrieve` → `call_model` ↔ `execute_tools`。
- ToolRegistry + Executor + `tavily_search`；后续加 tool 只注册即可。
- 模型根据 RAG context **自行决定** 是否调 Tavily（prompt 引导，非硬编码路由）。
- SSE/BFF/UI 支持 **多轮** tool；**`metadata.tool_steps` 持久化**，刷新后 ToolTimeline 可恢复（mirror `rag_sources`）。
- RAG 够时通常 0 轮 tool，行为接近 EP04。
- Mock ReAct：无 Key 时确定性模拟「弱 RAG → tool_calls → 再 generate」。
- `agent-langgraph.md` 作为 EP05 / L04 落地教材。

**Non-Goals:**

- chat/agent 双模式、`ChatCompletionRequest.mode`
- 系统规则强制 Tavily（`route_after_retrieve` 方案废弃）
- parallel tool calls、LLM Judge 节点

## Decisions

### D1: Unified ReAct 拓扑（取代固定编排）

```text
START
  → retrieve_knowledge          # 始终；写 retrieved_chunks；runner 发 sources SSE
  → call_model                  # ChatOpenAI.bind_tools([tavily_search, …])
  → should_continue
       ├─ 有 tool_calls ──► execute_tools ──► call_model ──┐
       │                                                    │
       └─ 无 tool_calls ──► END ◄───────────────────────────┘
```

- **扩展** `build_chat_graph()`；`recursion_limit = AGENT_MAX_ITERATIONS`（默认 5）。
- **retrieve 不在 tool 里重复**：RAG 由图入口固定完成；tools 补外部能力（Tavily）。

### D2: `rag_sufficient` — 提示用，不路由

retrieve 后计算：

- `rag_sufficient = len(chunks) > 0 and max(score) >= rag_chat_min_score`

写入 `ChatState`，注入 system prompt：

- sufficient：优先依据检索内容回答；仅当用户问题超出检索范围时再考虑 `tavily_search`。
- weak：明确告知检索不足，**应**使用 `tavily_search` 补充后再答。

**不**在图上用条件边强制 Tavily — 这是 ReAct 学习点（模型决策 + Harness 观测）。

### D3: Tool 层

```text
apps/api/app/tools/
  definitions.py
  registry.py
  executor.py
  builtin/tavily_search.py
```

- `execute_tools` 节点：读 AIMessage.tool_calls → `executor.run` → 追加 ToolMessage → 回 loop。
- 超时 10s；失败 → ToolMessage 含错误，不抛到 HTTP 层。

### D4: Mock ReAct（Harness / 无 Key）

| 场景 | Mock 行为 |
|:-----|:----------|
| RAG sufficient（ingest samples + 命中 query） | 直接流式 token，**无** tool_calls |
| RAG weak（无 ingest / 不命中 query） | 第 1 轮 AIMessage 带 `tool_calls: [tavily_search]` → execute（mock Tavily）→ 第 2 轮 token |

- 与 `mock_model` 模式一致；**零外网 LLM**。
- 真 Key 路径：真实模型 ReAct，行为由 prompt + tool description 塑造。

### D5: SSE 事件顺序

```text
start
  → sources?                    # retrieve 有 qualifying hits
  → (tool_call → tool_result)*  # 每轮 execute_tools 一对；可 0..N 轮
  → token*
  → done
```

- `done` 可含 `tool_steps: N` 供 UI/debug。
- 弱 RAG 且模型未调 tool：允许 no-hit 式回答（ReAct 风险，Harness + L3 后续优化）。

### D6: BFF / 前端

- 与 ep04 相同路径扩展 tool parts；timeline **支持多步**。
- 无 mode toggle；dev 展开 `tool_result.summary`；prod 折叠。
- RAG chips + timeline **可并存**（有 sources 且模型又调 Tavily 时）。
- **刷新保留 timeline**：流式靠 store；落库后靠 `metadata.tool_steps` + `hydrateHistoryToolSteps`（同 citation chips 双保险）。

### D6b: `metadata.tool_steps` 持久化

与 EP04 `metadata.rag_sources` 同一列、同一 `finalize_completion_stream` 事务：

```json
{
  "rag_sources": [ … ],
  "tool_steps": [
    {
      "id": "call_abc",
      "name": "tavily_search",
      "arguments": { "query": "…" },
      "success": true,
      "summary": "截断结果摘要（≤512 字）",
      "duration_ms": 840
    }
  ]
}
```

| 时机 | 行为 |
|:-----|:-----|
| 流式中 | Runner 累积 `stream_state.tool_steps`；每轮 SSE `tool_call`/`tool_result` |
| `finalize` | 有 tool 轮次则写 `metadata.tool_steps`；与 `rag_sources` 可并存 |
| Stop/interrupt | 已执行完的 tool 轮次仍持久化；未完成的最后一轮按已 emit 的 SSE 为准 |
| 列表 API | 已有 `MessageRead.metadata` 返回，无需新字段 |
| 前端 reload | `toUIMessages` / `hydrateHistoryToolSteps` 注入；`chat-message` store fallback |

- **summary 截断**：持久化上限 512 字符（比 dev UI 全文短，防 JSONB 膨胀）。
- **无 tool 轮次**：不写入 `tool_steps` 键（与无 `rag_sources` 一致）。

### D7: 容错

- 达 `recursion_limit`：用当前 messages 强制最终 `call_model`（`tool_choice=none`）或截断说明。
- Tavily 失败：ToolMessage 错误回灌，模型决定下一步（可能直接答或放弃）。

### D8: 配置

| 变量 | 默认 | 说明 |
|:-----|:-----|:-----|
| `AGENT_MAX_ITERATIONS` | 5 | LangGraph recursion_limit |
| `AGENT_TOOL_TIMEOUT_SECONDS` | 10 | Executor |
| `TAVILY_API_KEY` | 空 | 空则 mock Tavily |
| `AGENT_TOOLS_ENABLED` | true | false 回滚 EP04 纯 RAG 图（应急） |

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| 弱 RAG 模型不调 Tavily | prompt 强调 + tool description；Harness 断言 mock 路径；L3 统计留 EP09 |
| 强 RAG 误调 Tavily（成本） | tool description「仅当检索不足」；监控 |
| 多轮 tool 延迟 | recursion_limit；首 slice 仅 1 个 tool |
| 学习曲线 | `agent-langgraph.md` + 图内注释 + unit 测 should_continue |

## Migration Plan

1. `AGENT_TOOLS_ENABLED=true` 部署 API（默认 Unified ReAct）。
2. 配置 `TAVILY_API_KEY`（可选）。
3. 部署 web timeline。
4. 回滚：`AGENT_TOOLS_ENABLED=false` 恢复 retrieve→call_model 无 loop。

## Open Questions

- [x] Unified ReAct 一步到位（学习目标）
- [x] 无用户 mode
- [x] retrieve 固定先跑；Tavily 由模型 ReAct 触发
- [x] `tool_result.summary` — dev 可见；prod 折叠
- [x] **`metadata.tool_steps` 持久化** — 刷新 / `onFinish` sync 后 timeline 保留

## Future（加 tool 不改图）

- 注册 `db_readonly`、`web_search_searxng` 到 Registry + prompt 一句即可
- LLM Judge 节点、L3 pass rate
