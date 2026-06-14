## 0. Human review（apply 前必过）

> propose 完成后 **必须停在这里**等人审；未勾选前 **禁止**写业务代码。

- [x] **Tasks reviewed by human** — 人审通过后再 `/opsx:apply`、`/work-next` 或说「继续实现」

### Review checklist

- [x] 前后端成对：`GET/DELETE /api/v1/memories` ↔ `/memories` 页面 + 导航入口
- [x] Harness 覆盖：长历史 completion + memories API（design D1–D5 每条有对应 task）
- [x] Summary 节流：单会话长聊非每轮 summary（D3 increment + cooldown）
- [x] 与 `docs/tasks/epics/EP06-memory.md` Story 6.1–6.5 一致；无 EP07 工作流 scope
- [x] SSE / BFF 契约不变（裁剪仅图内，对外透明）
- [x] 每条 task ≤3 文件 / ~150 行

**Reviewer notes:**（可选）

**数据流：**

```text
POST /chat/completions
  → ChatService 全量 history → graph state
  → trim_history（token 预算）
  → load_user_memories（TopK 长期记忆）
  → retrieve_knowledge → call_model ↔ execute_tools
  → finalize → BackgroundTasks: summary + memory extract
```

---

## 1. Config & token utilities

- [x] 1.1 `MEMORY_*`、`MAX_CONTEXT_TOKENS`、`RESERVE_FOR_REPLY`、`SUMMARY_TRIGGER_TOKENS`、`SUMMARY_INCREMENT_TOKENS`、`SUMMARY_COOLDOWN_SECONDS` in `config.py`
  - 预计文件：1 · 层：`apps/api/app/core/config.py`

- [x] 1.2 `services/memory/token_counter.py` — tiktoken + model fallback
  - 预计文件：2 · 层：`token_counter.py` + `tests/unit/test_token_counter.py`

## 2. Short-term memory（Story 6.1）

- [x] 2.1 `services/memory/short_term.py` — `trim_messages()` 滑动窗口 + 预算；保留 system/记忆/RAG 占位接口
  - 预计文件：2 · 层：`short_term.py` + `tests/unit/test_short_term.py`

- [x] 2.2 `trim_history` 图节点 + `ChatState` 扩展（`context_summary`、`memory_snippets`、`trim_stats`）
  - 预计文件：3 · 层：`graphs/nodes/trim_history.py` + `chat_state.py` + `chat_graph.py`（`START → trim_history → retrieve`）

## 3. Schema & repository（Story 6.2 基础）

- [x] 3.1 Alembic：`memories` 表 + `conversations.context_summary` / `summary_updated_at`；更新 `docs/database.md`
  - 预计文件：2 · 层：`alembic/versions/` + `docs/database.md`

- [x] 3.2 `Memory` ORM + `MemoryRepository` + Pydantic schemas（`MemoryRead`）
  - 预计文件：3 · 层：`models/memory.py` + `repositories/memory_repository.py` + `schemas/memory.py`

## 4. LangGraph 记忆加载（Story 6.5）

- [x] 4.1 `load_user_memories` 节点 — embed 最近 human 查询 + TopK；写 `memory_snippets`
  - 预计文件：2 · 层：`graphs/nodes/load_user_memories.py` + `chat_graph.py` 边

- [x] 4.2 `call_model` 叠加 `context_summary` + `memory_snippets` system 块（与 RAG/ReAct prompt 分层）
  - 预计文件：2 · 层：`nodes/call_model.py` + `prompts/memory_context.py`

## 5. 会话摘要（Story 6.3）

- [x] 5.1 `summary_service.py` — `should_schedule_summary()`（首次 / increment / cooldown）+ rolling 合并（旧摘要 + `created_at > summary_updated_at` 的新消息）；mock LLM stub
  - 预计文件：2 · 层：`summary_service.py` + `tests/unit/test_summary_service.py`（含：超 4096 首次触发；cooldown 内跳过；increment 不足跳过；increment+cooldown 满足才触发）

- [x] 5.2 `chat_service.py` `finalize` 后仅当 `should_schedule_summary()` 为真时 `BackgroundTasks` 调度（不阻塞 SSE）
  - 预计文件：1 · 层：`services/chat_service.py`

## 6. 长期记忆抽取与检索（Story 6.2）

- [x] 6.1 `services/memory/long_term.py` — 抽取 JSON、upsert、embed、prune expired/low importance
  - 预计文件：2 · 层：`long_term.py` + `tests/unit/test_long_term.py`

- [x] 6.2 `chat_service` finalize 后调度 memory extract（与 summary 并列）
  - 预计文件：1 · 层：`services/chat_service.py`（与 5.2 可同 task 合并若 diff 仍 ≤150 行）

## 7. Memories API（Story 6.4）

- [x] 7.1 `GET /api/v1/memories` + `DELETE /api/v1/memories/{id}` + `memory_service.py` 薄层
  - 预计文件：3 · 层：`api/v1/memories.py` + `services/memory_service.py` + `main.py` 注册

- [x] 7.2 Harness `test_memories_api_contract.py`（list / delete / 403 跨用户）TDD 先写
  - 预计文件：1 · 层：`tests/harness/`

## 8. Harness 长历史（Story 6.1 + 6.5）

- [x] 8.1 Harness `test_memory_context_contract.py` — 种子 30+ 轮 mock 对话仍 200 + SSE 顺序不变
  - 预计文件：1 · 层：`tests/harness/`

## 9. 前端「我的记忆」（与 API 成对）

- [ ] 9.1 `lib/api-client.ts` memories 方法 + types
  - 预计文件：2 · 层：`lib/api-client.ts` + `lib/memory-types.ts`（或合入 `chat-types` 若更简）

- [ ] 9.2 `/memories` 页面：列表 + 删除确认 + 空态
  - 预计文件：2 · 层：`app/memories/page.tsx` + `components/memories/memory-list.tsx`

- [ ] 9.3 导航入口（`ChatHeader` 或 layout 用户菜单）链到 `/memories`
  - 预计文件：1–2 · 层：`components/chat/chat-header.tsx` 或 `app/layout.tsx`

## 10. Docs & closeout

- [ ] 10.1 `docs/tech/memory-system.md` — 三层记忆、图拓扑、配置、与 RAG 边界
  - 预计文件：1 · 层：`docs/tech/`

- [ ] 10.2 `pnpm test:api:harness` 全绿；勾选 `docs/tasks/epics/EP06-memory.md` + L05 相关项
  - 预计文件：epic/learning 勾选
