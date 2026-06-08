## Context

- **现状**：`ChatGraphRunner` 图 `START → call_model → END`；`KnowledgeSearchService` 仅 HTTP `/knowledge/search` 可调用。
- **数据**：本地需已 ingest Gold（Harness 用 `samples`；Demo 建议 `matches` + `samples` 或全量）。
- **约束**：Harness 无 Key → mock embed + mock LLM；有 Key → live embed + live LLM。检索与生成 **同一 Key 门控**。
- **BFF**：`memoryosSseResponseToTextStream` 仅转发 `token`，自定义 SSE 帧 **不会** 到达 AI SDK text stream——V1 溯源以 **prompt 生成 Markdown 参考来源** 为主；`sources` SSE 供 Harness / 直连 API 客户端。

## Goals / Non-Goals

**Goals:**

- 用户在世界杯相关问题聊天时，后端 **先检索** 再 **流式生成**，答案基于 fact cards。
- TopK 命中低于 `min_score` 时 **诚实兜底**（不捏造赛果/球员数据）。
- SSE 发出结构化 `sources`；助手正文含可读的「参考来源」列表。
- Harness 覆盖：有命中 / 无命中 / mock 全链路。

**Non-Goals:**

- 改 BFF 为 AI SDK data stream（structured citation chips → follow-up change）。
- DB migration 存 `message.sources`。
- 多轮对话自动改写 query、HyDE、Hybrid。
- 前端 collection 选择器。

## Decisions

### D1: 图拓扑

```text
START → retrieve_knowledge → call_model → END
```

- **为何不用 conditional**：V1 世界杯 Demo 默认 **始终 RAG**；`RAG_CHAT_ENABLED=false` 时 `retrieve` 短路为空（仍走同一图，便于 Harness 单测 retrieve）。
- **替代**：在 `ChatService` 内检索不入图 — 简单但不符合 Story 4.4「LangChain RAG Pipeline」叙事；弃用。

### D2: DB 注入 retrieve 节点

- `ChatGraphRunner.stream_tokens` / `astream_events` 的 `config["configurable"]` 传入 `db: AsyncSession`（与 `thread_id` 并列）。
- `retrieve_knowledge` 节点内 `KnowledgeSearchService(db)`；**禁止** 节点内新建 session（事务与 chat 同请求）。

### D3: Query 来源

- 取 **当前图 state 最后一条 `HumanMessage`** 的 `content` 作为检索 query（即本轮用户输入；regenerate 时 history 已含该 user 行）。

### D4: 检索参数（Settings）

| 变量 | 默认 | 说明 |
|:-----|:-----|:-----|
| `RAG_CHAT_ENABLED` | `true` | `false` 时 skip 检索 |
| `RAG_CHAT_TOP_K` | `5` | 传给 `KnowledgeSearchService.search` |
| `RAG_CHAT_MIN_SCORE` | `0.35` | 低于阈值的 chunk **不** 进 prompt / sources |
| `RAG_CHAT_COLLECTION` | `null` | 可选固定 collection；默认全库（与人审 B 一致） |

### D5: RAG Prompt

- 模块：`app/graphs/prompts/rag_chat.py`（或 `services/rag_prompt_service.py`）。
- System 消息结构：
  1. 角色：世界杯事实助手，**仅**依据「参考资料」回答。
  2. 注入过滤后的 chunk 文本 + `external_id` / `collection`。
  3. 要求：正文简洁；末尾 **Markdown `## 参考来源`** 列表（`- [external_id] snippet…`）。
  4. **无命中**（过滤后 0 条）：system 声明知识库无相关内容，请用户换问法；**禁止**编造比分/进球数。

### D6: SSE `sources` 事件

- 时机：`retrieve` 完成后、`token` 之前，由 `ChatService.stream_completion_events` 发出（Runner 返回 `retrieved_chunks` 或 graph state 字段）。
- 形状：

```json
{
  "event": "sources",
  "data": {
    "items": [
      {
        "external_id": "match:M-2022-64",
        "collection": "worldcup-samples",
        "entity_type": "match",
        "score": 0.82,
        "content_preview": "[Match] 2022 FIFA..."
      }
    ]
  }
}
```

- `done.data.sources` 重复同一列表（可选，便于客户端在流结束后绑定 `message_id`）。

### D7: Mock / Harness

- 与 `test_rag_contract` 相同：ingest `samples` + mock embed；query 用 **精确卡文** 或 design 固定句以保证 mock 召回。
- Live 冒烟：有 Key 时用语义 query（不强制改 Harness 默认 mock）。

### D8: 前端 V1

- **不** 改 BFF text stream 管线（限制与 follow-up 升级路线见 **[`docs/tech/chat-rag-stream.md`](../../../docs/tech/chat-rag-stream.md)**）。
- `markdown-body` / `chat-message`：对 `## 参考来源` 区块加样式（小字、折叠或可折叠 `<details>`）。
- Zustand 可缓存本轮 `sources` SSE（若直连测试）；主路径仍读 Markdown。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| BFF 丢弃 `sources` SSE | V1 依赖 Markdown 脚注；Harness 直连 FastAPI |
| `min_score` 过严导致频繁拒答 | 默认 0.35；§6 记录 dev 调参；Settings 可 env 覆盖 |
| 全库检索噪声（players 双命中） | 可选 `RAG_CHAT_COLLECTION`；prompt 要求合并重复球员 |
| Graph 节点拿 session 生命周期 | session 由 `ChatService` 请求 scope 提供，retrieve 同步 await |
| Mock LLM 不「理解」RAG context | Harness 断言 sources + 流式 token 非空；语义质量 live 人工抽测 |

## Migration Plan

1. 部署 API（无 migration）。
2. 确保目标环境已 ingest（CLI 或 `/knowledge/ingest/worldcup`）。
3. `RAG_CHAT_ENABLED=true`（默认）；回滚设 `false` 恢复纯 chat。

## Open Questions

- [ ] 人审：`RAG_CHAT_MIN_SCORE` 默认 **0.35** 是否接受？（可 dev 跑 3 条 query 后定案写入 `.env.example`）
- [ ] 人审：V1 是否 **强制** `RAG_CHAT_ENABLED=true`（无 UI 开关）？
- [ ] Follow-up change：**[`ep04-rag-chat-stream`](../../../docs/tech/chat-rag-stream.md)** — BFF Data Stream + citation chips + `messages.metadata` 持久化（方案已写入文档 §3–§4）
