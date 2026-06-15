## Why

EP02–EP05 将 **DB 全量历史** 原样注入 LangGraph，长对话会撑爆 context window、拉高成本与延迟，且模型无法跨会话记住用户偏好。EP06 要在不破坏现有 RAG/ReAct/SSE 契约的前提下，建立 **短期裁剪 + 会话摘要 + 长期记忆** 三层体系，并嵌入统一对话图。

## What Changes

- **Token 预算与计数**：`tiktoken`（模型名映射 + 中英 fallback）；配置 `MAX_CONTEXT_TOKENS`、`RESERVE_FOR_REPLY`、`MEMORY_*` 开关。
- **短期记忆**：滑动窗口 + token 预算裁剪；**system / 注入记忆 / RAG 上下文永不裁**；在图入口 `trim_history` 节点执行（DB 仍存全量）。
- **会话摘要**：`conversations.context_summary`；**首次**全量超 `SUMMARY_TRIGGER_TOKENS` 后异步生成；**后续**仅当增量 token + cooldown 满足时 rolling 合并（避免单会话长聊每轮 summary）。
- **长期记忆**：`memories` 表（type、content、importance、embedding、expires_at）；回合结束后 **异步抽取** 偏好/事实；向量 TopK 检索注入 system（复用现有 `EmbeddingService` + pgvector，非独立 LlamaIndex 服务）。
- **生命周期**：用户 `GET/DELETE /api/v1/memories`；过期与低 importance 清理策略。
- **LangGraph**：`START → trim_history → retrieve → call_model ↔ execute_tools`；`call_model` system 叠加长期记忆片段 + 会话摘要。
- **前端**：「我的记忆」页（列表 + 删除），与 memories API 成对。
- **Harness**：长历史 completion 契约 + memories CRUD 契约；现有 RAG/ReAct/Stop 回归。
- **文档**：`docs/tech/memory-system.md`；更新 EP06 Story 6.1–6.5。

**Non-Goals（本 change 不做）：**

- EP07 可视化工作流 / 简历 Demo
- 独立 LlamaIndex 微服务或第二套向量库集群
- Celery/ARQ 队列（首版 `BackgroundTasks` + 可选后续 change）→ **EP11**
- 记忆抽取的用户确认 UI、置信度人工审核流 → **EP10 Story 10.6** / **EP12** 数据基础
- 修改 SSE 帧类型或 BFF Data Stream 协议（内部 context 变化对外透明）
- Playwright E2E

## Capabilities

### New Capabilities

- `memory-system`: Token 预算、短期裁剪、会话摘要、长期记忆表与检索、异步抽取、LangGraph 节点、memories HTTP API

### Modified Capabilities

- `core-schema`: 新增 `memories` 表；`conversations` 增加 `context_summary`（及可选 `summary_updated_at`）

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/app/services/memory/` | `token_counter`、`short_term`、`summary`、`long_term`、`memory_service` |
| `apps/api/app/graphs/` | `trim_history` 节点；`chat_graph.py` 拓扑；`call_model` system 叠加记忆 |
| `apps/api/app/models/` · `repositories/` | `Memory`；`Conversation` 摘要字段 |
| `apps/api/app/api/v1/` | `memories.py` 路由 |
| `apps/api/app/services/chat_service.py` | 构图前/后挂接 trim；`finalize` 后触发摘要+抽取 |
| `apps/api/app/core/config.py` | 记忆与 token 预算配置 |
| `apps/api/tests/harness/` | `test_memory_context_contract.py`、`test_memories_api_contract.py` |
| `apps/api/tests/unit/` | short_term、token_counter、summary 单测 |
| `apps/web/` | `/memories` 页、`api-client`、导航入口 |
| `docs/tech/memory-system.md` | 架构与学习要点 |
| 依赖 | `tiktoken`（requirements） |
