## Context

- **现状**：`ChatService._to_graph_state` 将 `messages` 表全量转为 LangChain messages；EP05 图 `retrieve → call_model ↔ execute_tools`；RAG system 与 tool guidance 在 `call_model` 动态注入。
- **约束**：SSE / BFF / 前端消息列表 **仍展示 DB 全量**；裁剪仅影响 **发给 LLM 的 state**。
- **依赖**：EP02 流式、EP03 JWT + schema、EP04 RAG、EP05 ReAct；Embedding 与 pgvector 已用于知识库。

## Goals / Non-Goals

**Goals:**

- 可配置的 global token 预算；超长对话稳定 completion（不触发 provider context 报错）。
- 短期：保留最近 N 轮且在预算内；system、记忆注入、RAG 块优先保留。
- 中期：会话级 rolling summary 降低重复 token。
- 长期：跨会话用户事实/偏好检索注入；用户可查看与删除。
- LangGraph 单图扩展，不 fork EP04/EP05 两套图。
- Harness 可证明「50+ 轮 mock 对话仍可完成」与 memories API 契约。

**Non-Goals:**

- 记忆与 RAG 知识库写入打通（长期记忆 **用户域**，RAG **世界杯事实域**，检索路径分离）。
- 实时同步摘要（首版摘要 **异步**，不阻塞首 token）。
- EP09 phase UI / LLM-as-judge。

## Decisions

### D1: 裁剪在图内 `trim_history` 节点

**选择**：`START → trim_history → retrieve → …`  
**理由**：与 L05「LangGraph 节点组装 messages 前裁剪」一致；`chat_service` 仍传全量 history，便于测试与审计。  
**备选**：在 `chat_service._to_graph_state` 裁剪 — 图外逻辑分散，ReAct 多轮 tool 回灌后难统一重裁。

### D2: Token 计数

**选择**：`tiktoken` + `cl100k_base` fallback；按 `settings.openai_model` 映射 encoding（未知模型用 fallback）。  
**预算分配**（可配置，默认示意）：

```text
MAX_CONTEXT_TOKENS (e.g. 8192)
  - RESERVE_FOR_REPLY (e.g. 1024)
  - system + memory_snippets + rag_system (measure, never drop)
  - context_summary block (keep if present)
  - recent Human/AI/Tool turns (trim oldest first)
```

### D3: 会话摘要存储与节流

**选择**：`conversations.context_summary` TEXT + `summary_updated_at`；摘要作为 **单独 SystemMessage 前缀**（`[会话摘要] …`），不与 RAG grounded prompt 混写。

**产品背景**：当前默认 **单会话长聊**（登录恢复最近一场；「新建分析」可选）。若仅「全量 token > 4096 且每轮 finalize 就摘要」，超长会话会 **几乎每轮调一次 summary LLM** — 不可接受。

**触发（`should_schedule_summary`，finalize 后、BackgroundTasks 前判定）**：

| 阶段 | 条件（全部满足才 schedule） |
|:-----|:----------------------------|
| **首次摘要** | `context_summary` 为空 **且** 全量历史 token > `SUMMARY_TRIGGER_TOKENS` |
| **后续更新** | `context_summary` 非空 **且** 自 `summary_updated_at` 以来新增消息 token ≥ `SUMMARY_INCREMENT_TOKENS` **且** 距 `summary_updated_at` ≥ `SUMMARY_COOLDOWN_SECONDS` |

不满足 → **跳过**（短会话零摘要；长单会话 **偶尔** 更新，非每轮）。

**Rolling 输入**（非每轮重扫全量）：

```text
LLM 输入 = 现有 context_summary（若有）
         + 仅 created_at > summary_updated_at 的新增 Human/Assistant 消息
Prompt 要求：合并为更短摘要，保留用户约束/待办/决策
```

**执行**：`BackgroundTasks` 异步；mock LLM 写确定性 stub；**不阻塞** SSE。

**新会话**：新建 `conversation` → `context_summary` / `summary_updated_at` 均为空 → 重新走「首次摘要」规则。

### D4: 长期记忆表与检索

**选择**：PostgreSQL `memories` + pgvector `embedding`（维度与 RAG 一致）；类型 `preference | fact | constraint`；`importance` 0–1；可选 `expires_at`。  
**抽取**：`finalize` 后异步 LLM 输出 JSON 列表；同 `key`/`type` 冲突则 **覆盖** 旧行（upsert by user_id + normalized key）。  
**检索**：每轮 `load_user_memories` 节点（在 `trim_history` 之后）对用户最新 human 文本 embed，TopK cosine；注入 system `## 用户长期记忆`。  
**LlamaIndex**：不另起服务；epic「专属索引」落为 **memories 表向量列 + 独立 collection 语义**（`memory:{user_id}` 过滤）。

### D5: 生命周期

- `GET /api/v1/memories` — 分页列表（不含 embedding 向量）。
- `DELETE /api/v1/memories/{id}` — 仅本人。
- 清理：`expires_at < now()` 或 `importance < MEMORY_PRUNE_THRESHOLD` 在抽取任务末尾批量删。

### D6: 功能开关

| 变量 | 默认 | 说明 |
|:-----|:-----|:-----|
| `MEMORY_ENABLED` | true | false → 跳过 trim/load/extract（回滚 EP05 行为） |
| `MEMORY_SHORT_TERM_ENABLED` | true | 仅关短期裁剪 |
| `MEMORY_LONG_TERM_ENABLED` | true | 关长期表读写 |
| `MEMORY_LONG_TERM_TOP_K` | 5 | 每轮长期记忆 TopK |
| `MEMORY_MIN_SCORE` | 0.35 | 注入记忆的最低相似度（cosine） |
| `MAX_CONTEXT_TOKENS` | 8192 | 发给 LLM 的上限 |
| `RESERVE_FOR_REPLY` | 1024 | 预留给生成 |
| `SUMMARY_TRIGGER_TOKENS` | 4096 | **首次**摘要：全量历史须超此值 |
| `SUMMARY_INCREMENT_TOKENS` | 1024 | **后续**更新：自上次摘要以来新增消息至少这么多 token |
| `SUMMARY_COOLDOWN_SECONDS` | 300 | **后续**更新：距 `summary_updated_at` 至少间隔（秒） |

### D7: ChatState 扩展

```python
context_summary: NotRequired[str | None]
memory_snippets: NotRequired[list[dict[str, Any]]]  # {type, content, score}
trim_stats: NotRequired[dict[str, Any]]  # dropped_turns, token_count — debug/LangSmith
```

`trim_history` 写回 `messages`（裁剪后列表）；`load_user_memories` 写 `memory_snippets`；`call_model` 合并进 system。

### D8: 前端

- 路由 `/memories`（需登录）；表格：类型、内容摘要、时间、删除。
- `ChatHeader` 或用户菜单增加「我的记忆」链接。
- **无**记忆编辑（首版只读+删）；**无**在聊天页展示 memory chips（避免噪音，EP09 可考虑 phase UI）。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| 裁剪掉关键约束 | 摘要 prompt 强调用户约束；`constraint` 类型长期记忆优先注入 |
| 抽取幻觉写入记忆 | mock 路径固定 stub；真 LLM 限制条数 + importance 默认 0.5；用户可删 |
| 摘要异步滞后 | 下一轮才生效；可接受（design 非热路径） |
| 单会话长聊每轮 summary | D3 节流：increment + cooldown；rolling 增量输入 |
| ToolMessage 被裁掉导致 ReAct 断链 | 裁剪保留 **最近完整 assistant+tool 轮次**；不单删 ToolMessage |
| 与 RAG token 争抢 | 先量 system 块，再裁 history；超限时丢最旧 turn 而非砍 RAG |

## Migration Plan

1. Alembic migration：`memories` + `conversations.context_summary`。
2. 部署 API，`MEMORY_ENABLED=true`（默认）。
3. 部署 web `/memories`。
4. 回滚：`MEMORY_ENABLED=false` 恢复全量 history 入图。

## Open Questions

- [ ] 首版 `MAX_CONTEXT_TOKENS` 默认值是否跟 qwen-turbo 产品上限对齐（人审可改 config 默认）。
- [ ] 是否在 dev 暴露 `trim_stats` 到 SSE metadata（建议 **否**，留 LangSmith；生产指标见 **EP11**）。
- [x] 单会话长聊 summary 频率 → D3 increment + cooldown（已决）

## 后续史诗（MVP 后补全）

企业级差距项不在本 change 落地，已记入 backlog：

| 史诗 | 内容 |
|:-----|:-----|
| [EP11 — 记忆运维补强](../tasks/epics/EP11-memory-ops.md) | 异步任务队列、记忆溯源、监控指标 |
| [EP12 — 记忆质量评测](../tasks/epics/EP12-memory-eval.md) | 离线评测集、摘要/裁剪/抽取回归、可选 LLM-as-judge |
| [EP13 — 分布式与 Remote 热插拔](../tasks/epics/EP13-memory-distributed.md) | Compose 多容器、注册表、`langgraph` remote |
| [EP14 — K8s 与腾讯云](../tasks/epics/EP14-k8s-cloud.md) | k3d/Helm、TKE、Ingress+SSE |

总览：[post-mvp-roadmap.md](../tasks/post-mvp-roadmap.md)
