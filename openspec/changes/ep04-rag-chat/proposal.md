## Why

`ep04-rag` 已交付 Gold 摄入与 `POST /knowledge/search`，但聊天仍走 **无检索** 的 `START → call_model → END`，无法完成 EP04 Story 4.4「快速问答 Demo」与 Story 4.6「答案溯源 / 无命中兜底」。本 change 把 **向量检索接入 LangGraph**，在现有 SSE 聊天链路上生成带引用的事实卡回答。

## What Changes

- LangGraph 增加 **`retrieve`** 节点：用用户最新问题调 `KnowledgeSearchService`（复用 mock/live embedding 双模式）。
- **`call_model`** 前注入 RAG system prompt（TopK 片段 + 引用规则 + 无命中兜底话术）。
- Settings：`RAG_CHAT_ENABLED`、`RAG_CHAT_TOP_K`、`RAG_CHAT_MIN_SCORE`（可调阈值拒答）。
- SSE 新增 **`sources`** 事件（检索命中列表，Harness 可断言）；`done` 可选携带相同摘要供客户端持久化。
- Harness `test_rag_chat_contract.py`：mock ingest + mock/live LLM 路径下断言检索命中与流式回答。
- 前端 **最小溯源**：助手 Markdown 中「参考来源」区块可读展示（prompt 驱动）；**不做** BFF data-stream 大改（structured chips 留 follow-up，方案见 [`docs/tech/chat-rag-stream.md`](../../docs/tech/chat-rag-stream.md)）。
- 更新 `docs/tasks/epics/EP04-rag.md` Story 4.4 / 4.6 首项勾选。

**Non-Goals（本 change 不做）：**

- Hybrid / 重排 / Query 改写（EP04-03）
- 新 ingest 格式、上传解析（Story 4.1–4.2）
- LlamaIndex 双栈（Story 4.5、4.7）
- `messages` 表 JSONB 持久化引用（V1 会话内 SSE + Markdown 脚注；reload 后结构化 sources 可丢）
- 聊天页切换 collection / 高级检索 UI

## Capabilities

### New Capabilities

- `rag-chat`: LangGraph 检索增强生成、RAG prompt、SSE sources、无命中兜底

### Modified Capabilities

- `chat-sse`: SSE 事件流增加 `sources`（及 `done.data.sources` 可选字段）
- `chat-ui`: 助手消息展示 RAG「参考来源」Markdown 区块（样式/折叠）

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/app/graphs/` | `ChatState`、`retrieve` 节点、图拓扑 |
| `apps/api/app/services/` | `chat_service.py` 发 `sources`；可选 `rag_prompt.py` |
| `apps/api/app/core/config.py` | RAG chat settings |
| `apps/api/tests/harness/` | `test_rag_chat_contract.py` |
| `apps/web/components/chat/` | Markdown 来源区展示 |
| `openspec/specs/` | 新增 `rag-chat`；delta `chat-sse`、`chat-ui` |
| 依赖 | 无新包；复用 `KnowledgeSearchService`、`EmbeddingService` |
