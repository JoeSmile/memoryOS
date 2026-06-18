---
name: codebase-orient
description: >-
  Read-only codebase orientation for MemoryOS. Use when the user or agent needs
  to understand project structure, find where to change Chat/SSE/RAG/Agent/Memory,
  onboard to the monorepo, or asks 代码结构/在哪改/代码地图 before implementing.
---

# Codebase Orient — MemoryOS 只读导航

**立场**：先读地图，再搜代码；**本 skill 阶段不写业务代码**（除非用户明确说「开始实现」并已过 OpenSpec / work-next 门禁）。

---

## 1. 必读（按顺序）

1. **[docs/tech/code-map.md](../../docs/tech/code-map.md)** — 全仓 mental model、Chat 三层链路、文件索引
2. 按任务选读：
   - 后端：`docs/tech/BE-engineering.md`
   - 前端：`docs/tech/FE-engineering.md`
   - Chat SSE / BFF：`docs/tech/chat-rag-stream.md` · `docs/tech/chat-stream-cancel.md`
   - LangGraph / Agent：`docs/tech/langgraph-chat.md` · `docs/tech/agent-langgraph.md`
   - 安全：`docs/tech/chat-security.md`

---

## 2. 用户意图 → 入口文件

| 用户说的 | 先打开 |
|:---------|:--------|
| 聊天流式 / SSE 假死 / token 不显示 | `code-map.md` §3 → `chat.py` · `chat_service.py` · `memoryos-upstream.ts` · `use-chat-session.ts` |
| Stop / 取消生成 | `chat-stream-cancel.md` · `chat/cancel/route.ts` · `StreamCancelCache` |
| RAG 引用 / sources chips | `chat-rag-stream.md` · `retrieve.py` · `sse-frames.ts` |
| Agent / 工具调用 | `runner.py` · `execute_tools.py` · `tools/` |
| 记忆写入 / 召回 | `services/memory/` · `load_user_memories.py` · `memory-system.md` |
| 登录 / JWT | `api/v1/auth.py` · `deps.py` · `apps/web/lib/auth-token.ts` |
| 限流 / 配额 | `rate_limit.py` · `token_quota_service.py` |
| 世界杯 Demo | `worldcup.py` · `demo/` · `wc2022_analysis_presets.py` |

---

## 3. 调查步骤（只读）

1. 从 **code-map §3** 确认改动落在 API / BFF / UI 哪一层。
2. **SemanticSearch 或 Grep** 只搜该层；跨层问题画出 data flow 再往下搜。
3. 动 API 契约时，在 `apps/api/tests/harness/` 找对应 `*_contract.py`。
4. 动 BFF 转换时，看 `apps/web/tests/unit/test_memoryos_data_stream.test.ts`。
5. 输出给用户：
   - 3～5 句结构摘要
   - 相关文件列表（带路径）
   - 推荐 docs / harness
   - **若需改代码**：提醒走 `work-next` 或 `openspec-apply-change`，不要在本 skill 里直接改 `apps/`（OpenSpec 门禁除外）。

---

## 4. Chat SSE 红线（orient 时顺带检查）

改 `apps/api/app/api/v1/chat.py` 或 BFF stream 时，对照 code-map：

- SSE 路由 **不要** `Depends(get_db/get_redis)` 挂全程
- Graph 节点用 **`graph_db_session`**，不要借 stream 的 session
- `InjectionGuardMiddleware` 的 `replay_receive` 必须 **delegate 原始 receive**
- 流结束后任务用 **detached `asyncio.create_task`**，不用 `BackgroundTasks` 挡 HTTP 收尾
- BFF `memoryosSseResponseToDataStream`：**增量 pull** + token 合并，避免一次灌满队列

---

## 5. 与其它 skill 的分工

| Skill | 何时用 |
|:------|:--------|
| **codebase-orient**（本 skill） | 懂结构、找文件、改前导航 |
| **openspec-explore** | 需求不清、方案对比、不写码的探讨 |
| **work-next** | 按 OpenSpec task 正式实现 |
| **systematic-debugging** | 已有失败现象、要 runtime 证据 |

---

## 6. 可选 MCP（仓库外）

若已配置本地 MCP（如 codebase-mcp、Nexus-MCP），可在本 skill 调查阶段用于 **symbols / call graph**；仍以 `code-map.md` 为权威索引，MCP 结果与文档冲突时以代码为准并建议更新 code-map。
