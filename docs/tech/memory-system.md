# 多层级记忆系统（EP06）

> **状态**：`ep06-memory` 已落地 — 与 `apps/api/app/graphs/`、`services/memory/` 对齐。  
> **学习**：[L05 Part A](../tasks/learning/L05-memory-workflow.md)  
> **设计细节与时序**：[ep06-memory-design.md](./ep06-memory-design.md)  
> **OpenSpec**：[`ep06-memory`](../../openspec/changes/ep06-memory/)

---

## 1. 三层记忆

| 层 | 存储 | 作用时机 | 实现 |
|:---|:-----|:---------|:-----|
| **短期** | 无独立表；裁剪后 `ChatState.messages` | 每轮进图前 | `trim_history` + `short_term.trim_messages()` |
| **中期（会话摘要）** | `conversations.context_summary` + `summary_updated_at` | 下一轮注入 system | `summary_service` + finalize 后 `BackgroundTasks` |
| **长期** | `memories` 表 + pgvector | 每轮检索注入；finalize 后异步抽取 | `load_user_memories` + `long_term` |

**约束**：`messages` 表与列表 API **始终全量**；裁剪只影响发给 LLM 的 state。SSE / BFF 契约与 EP05 一致。

---

## 2. 图拓扑（EP06 后）

`AGENT_TOOLS_ENABLED=true`（默认 ReAct）：

```text
START → trim_history → load_user_memories → retrieve_knowledge → call_model
                                                                  ↓
                                            execute_tools ← (tool_calls)
                                                  ↓
                                            call_model → END
```

`AGENT_TOOLS_ENABLED=false`（RAG-only）：`call_model → END`，无 `execute_tools`。

`call_model` 内 system 分层（由 `prompts/memory_context.py` 组装）：

1. `[会话摘要]`（若有 `context_summary`）
2. `## 用户长期记忆`（若有 `memory_snippets`）
3. RAG grounded prompt / ReAct tool guidance（EP04/EP05）

---

## 3. Token 预算

计数：`services/memory/token_counter.py`（tiktoken，`openai_model` 映射，未知模型用 `cl100k_base`）。

```text
MAX_CONTEXT_TOKENS
  − RESERVE_FOR_REPLY          # 预留给 assistant 生成
  − system 块（摘要 + 长期记忆 + RAG，实测不裁）
  − context_summary 占位
  − 最近 Human/AI/Tool 轮（从最旧 turn 删起）
```

`trim_history` 保留最近完整 assistant+tool 轮，避免 ReAct 断链。

---

## 4. 配置（`.env`）

| 变量 | 默认 | 说明 |
|:-----|:-----|:-----|
| `MEMORY_ENABLED` | `true` | `false` → 跳过 trim/load/extract，行为回退 EP05 |
| `MEMORY_SHORT_TERM_ENABLED` | `true` | 关短期裁剪 |
| `MEMORY_LONG_TERM_ENABLED` | `true` | 关长期表读写与抽取 |
| `MEMORY_LONG_TERM_TOP_K` | `5` | 每轮注入 TopK |
| `MEMORY_MIN_SCORE` | `0.35` | 注入最低 cosine 相似度 |
| `MEMORY_PRUNE_THRESHOLD` | `0.1` | 抽取任务末尾清理低 importance |
| `MAX_CONTEXT_TOKENS` | `8192` | 发给 LLM 的上限 |
| `RESERVE_FOR_REPLY` | `1024` | 预留给生成 |
| `SUMMARY_TRIGGER_TOKENS` | `4096` | 首次摘要：全量历史须超此 token |
| `SUMMARY_INCREMENT_TOKENS` | `1024` | 滚动摘要：新增消息至少这么多 token |
| `SUMMARY_COOLDOWN_SECONDS` | `300` | 滚动摘要：距上次更新至少间隔（秒） |

ReAct 图在 `memory_enabled` 时 `recursion_limit = AGENT_MAX_ITERATIONS + 2`（EP06 前置节点开销），见 `graphs/runner.py`。

---

## 5. 与 RAG 的边界

| 维度 | 长期记忆（用户域） | RAG 知识库（世界杯事实域） |
|:-----|:-------------------|:---------------------------|
| 存储 | `memories` + `user_id` | `documents` / 知识集合 |
| 写入 | finalize 后 LLM 抽取 | ingest API / 脚本 |
| 检索节点 | `load_user_memories` | `retrieve_knowledge` |
| 注入块 | `## 用户长期记忆` | RAG grounded system |
| 前端 | `/memories` 列表与删除 | 聊天内 sources chip |

**不**把用户记忆写入 RAG collection；**不**在 RAG 检索里查 `memories` 表。

---

## 6. HTTP API 与前端

| API | 说明 |
|:----|:-----|
| `GET /api/v1/memories` | 当前用户列表（无 embedding）；`limit` / `offset` |
| `DELETE /api/v1/memories/{id}` | 仅本人；跨用户 → `404` / `memory_not_found` |

Web：`/memories` 页面；`ChatHeader` →「我的记忆」。客户端见 `apps/web/lib/api-client.ts`（`listMemories` / `deleteMemory`）。

---

## 7. 异步任务（首版）

finalize 且 `COMPLETION_COMPLETE` 后，经 FastAPI `BackgroundTasks` 登记（**不阻塞** SSE `done`）：

- `run_summary_background` — 节流后更新 `context_summary`
- `run_extract_background` — 长期记忆抽取 + prune

响应发送完毕后执行；摘要/记忆 **下一轮** 才进入图 state。生产级队列见 [EP11](../tasks/epics/EP11-memory-ops.md)。

---

## 8. 回滚

`MEMORY_ENABLED=false`：图跳过 trim/load；`chat_service` 不调度 summary/extract；全量 history 入图（与 EP05 一致）。

---

## 9. 代码索引

| 路径 | 职责 |
|:-----|:-----|
| `graphs/nodes/trim_history.py` | 短期裁剪 |
| `graphs/nodes/load_user_memories.py` | 长期 TopK |
| `graphs/nodes/call_model.py` | system 分层 |
| `graphs/prompts/memory_context.py` | 摘要/记忆 prompt 块 |
| `services/memory/summary_service.py` | 摘要调度与生成 |
| `services/memory/long_term.py` | 抽取 / upsert / prune |
| `services/chat_service.py` | 构图、`context_summary`、BackgroundTasks |
| `repositories/memory_repository.py` | CRUD + 向量检索 |

Harness：`test_memory_context_contract.py`、`test_memories_api_contract.py`。
