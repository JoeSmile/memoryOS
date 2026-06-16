## Why

EP02–EP08 已交付可用的聊天、RAG、Agent 与 Docker 部署，但 **生产级安全、成本、限流与过程态 UX** 仍缺：用户发送后 retrieve/tool 阶段常静默；无 Prompt 注入与 RAG 内容清洗；无 Token 统计与配额；无限流与审计；无组件降级策略。EP09 在 **不新增业务功能** 的前提下，补齐企业可运维的防护、性能与可观测基线。

## What Changes

- **Story 9.1 安全**：用户输入快失败（422）+ 自研 `rag_sanitizer`（ETL/retrieve 共用）+ `<POLICY>`/`<DOCS>` 分层 system prompt；输入长度限制。
- **Story 9.2 性能**：Embedding 结果缓存、可选 LLM 响应缓存键、慢查询与索引复查文档化 + 必要 migration。
- **Story 9.3 Token 与成本**：从 OpenAI-compatible usage 落库；按 user/day 聚合；超配额 429；可选简单用量 API。
- **Story 9.4 限流与审计**：Redis 滑动窗口（登录 / chat / demo-turn）；关键操作审计日志表与写入。
- **Story 9.5 降级**：LLM 主备路由、Redis 不可用降级、向量检索失败时仅 LLM 路径。
- **Story 9.6 架构图**：`docs/architecture/` 三张图（系统总览、RAG、Agent）。
- **Story 9.7 LangSmith**：生产采样率 env、错误 100% 采样策略文档。
- **Story 9.8 Agent 过程态 UI**：
  - **L1**（brownfield）：`submitted`/demo 等待 Thinking 占位 — 已部分落地，本 change 验收与 polish。
  - **L2**：Runner 发 `phase` SSE → BFF → `AgentPhaseIndicator`。
  - **L3**：ToolTimeline pending 行、可选折叠「思考过程」。

**Non-Goals：**

- 新 Agent 工具、新 RAG 数据源、WC 业务功能
- 完整计费/发票系统、WAF 级 DLP
- K8s HPA / 自动扩缩（→ EP14）
- httpOnly Cookie 迁移（可文档预留，非本 change 必做）

## Capabilities

### New Capabilities

- `chat-security`: 输入快失败、用户注入检测、自研 `rag_sanitizer`（ETL+retrieve）、POLICY/DOCS 分层 prompt
- `token-usage`: Token 落库、配额、429 与可选用量查询
- `rate-limit-audit`: Redis 滑动窗口限流与操作审计
- `service-degradation`: LLM/Redis/向量检索降级矩阵
- `performance-cache`: Embedding/LLM 缓存与 DB 索引优化
- `agent-phase-ui`: SSE `phase` 事件与前端过程态指示

### Modified Capabilities

- `chat-ui`: Thinking/phase 占位、composer 与 streaming 联动、demo 消息无 regenerate
- `chat-sse`: 新增 `phase` 帧类型与顺序约束
- `rag-retrieval`: ingest 与 retrieve 双点 sanitization（共用 `rag_sanitizer`）

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/app/services/security/` | ETL + retrieve 共用清洗；**北向** Guard；EP13 可 import |
| `apps/api/app/graphs/prompts/rag_chat.py` | `<POLICY>` + `<DOCS>` 分层 |
| `docs/tech/chat-security.md` | 威胁模型与纵深防御说明 |
| `apps/api/app/services/chat_service.py` · `graphs/runner.py` | phase SSE、降级、usage 落库 |
| `apps/api/app/services/embedding_service.py` | 缓存层 |
| `apps/api/app/repositories/` · Alembic | `token_usage`、`audit_log` 表 |
| `apps/web/components/chat/` | `AgentPhaseIndicator`、ToolTimeline pending |
| `docs/architecture/` · `docs/tech/` | 架构图、LangSmith 生产策略 |
| `docs/tasks/epics/EP09-optimization.md` | Story 9.1–9.8 勾选 |
| Harness | 安全/限流/phase/token 契约测试 |
