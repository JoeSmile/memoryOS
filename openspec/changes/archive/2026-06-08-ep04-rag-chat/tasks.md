## 0. Human review（apply 前必过）

> propose 完成后 **必须停在这里**等人审；未勾选前 **禁止** 写业务代码。

- [x] **Tasks reviewed by human** — 人审通过后再 `/opsx:apply`、`/work-next` 或说「继续实现」

### Review checklist

- [x] Harness 覆盖 design D6/D7（sources SSE、mock 全链路、无命中兜底）
- [x] 与 EP04 Story 4.4「快速问答 Demo」、4.6「溯源 + 无命中」首 slice 一致
- [x] 明确 V1 **不**改 BFF data stream；Markdown 溯源可接受
- [x] 每条 task ≤3 文件 / ~150 行

**Reviewer notes:**

- **依赖**：`ep04-rag` ✅ archive；本地需已 ingest（Harness 自灌 `samples`）。
- **默认**：`RAG_CHAT_ENABLED=true` · `TOP_K=5` · `MIN_SCORE=0.35` · collection 全库。
- **人审待定**：`MIN_SCORE` 默认值 · 是否允许 env 关闭 RAG。
- **BFF 升级（本 change 不做）**：已写入 [`docs/tech/chat-rag-stream.md`](../../../docs/tech/chat-rag-stream.md) — follow-up **`ep04-rag-chat-stream`**

---

## 1. Settings

- [x] 1.1 `Settings` 增加 `rag_chat_enabled` / `top_k` / `min_score` / `collection` + `.env.example`
  - 预计文件：2 · 层：`core/config` + `.env.example`

## 2. RAG prompt

- [x] 2.1 `rag_chat_prompt.py`：build system message（有命中 / 无命中两模板）
  - 预计文件：1 · 层：`graphs/prompts`

## 3. LangGraph retrieve

- [x] 3.1 `ChatState` 增加 `retrieved_chunks`；`retrieve_knowledge` 节点 + 图拓扑
  - 预计文件：3 · 层：`graphs/`（`chat_state.py`、`nodes/retrieve.py`、`chat_graph.py`）

- [x] 3.2 `ChatGraphRunner` 注入 `db` 到 `configurable`；`call_model` 消费 RAG system prompt
  - 预计文件：2 · 层：`graphs/runner.py`、`nodes/call_model.py`

## 4. Chat SSE

- [x] 4.1 `ChatService.stream_completion_events` 发 `sources`（及 `done.data.sources`）；Runner 回传检索结果
  - 预计文件：2 · 层：`services/chat_service.py`、`graphs/runner.py`

## 5. Harness

- [x] 5.1 `tests/harness/test_rag_chat_contract.py`：ingest samples → chat → assert sources + tokens + no-hit case
  - 预计文件：1 · 层：`tests/harness`（TDD 先写）

## 6. Frontend（最小溯源 UI）

- [x] 6.1 `chat-message` / `markdown-body`：样式化 `## 参考来源` 区块（折叠或小字）
  - 预计文件：2 · 层：`apps/web/components/chat`

## 7. Closeout

- [x] 7.1 `pnpm test:api:harness` 全绿；勾选 `docs/tasks/epics/EP04-rag.md` Story 4.4/4.6 首项
  - 预计文件：1 · 层：`docs/epic`

- [x] 7.2 archive change
  - 预计文件：0 · openspec archive
