## 0. Human review（apply 前必过）

> propose 完成后 **必须停在这里**等人审；未勾选前 **禁止**写业务代码。

- [x] **Tasks reviewed by human** — 人审通过后再 `/opsx:apply`、`/work-next` 或说「继续实现」

### Review checklist

- [x] Story 9.1 含 **rag_sanitizer 自研 + ETL/retrieve 共用 + POLICY/DOCS 分层 prompt + 第三方包 adapter 试用（默认关）**
- [x] 安全 / 限流 / Token API 有 Harness；phase SSE 有 contract + Web 映射单测
- [x] **北向治理**：422/429/audit 在 API 路由层；`services/security/` 可 import；Token 经 `UsageRecorder` 预留 remote（§12）
- [x] L1 Thinking brownfield 仅验收/polish task，不与 L2 重复造轮子
- [x] 前后端成对（phase SSE ↔ AgentPhaseIndicator；usage API ↔ 可选 FE 提示）
- [x] 每条 task ≤3 文件 / ~150 行

**Reviewer notes:**

---

## 1. Story 9.8 L1 — Thinking 占位验收（brownfield）

- [x] 1.1 验收现有 `ChatThinkingIndicator`：`isSending && !isStreaming`、流式空 assistant 文案
  - 预计文件：2 · 层：`chat-message-list.tsx` + `chat-message.tsx`（仅 polish）
  - 验收：demo 点击「开始分析」≤300ms 出现占位；LLM 流式无底部重复 indicator

- [x] 1.2 Composer：`Stop` 仅绑 `isStreaming`；`isSending` 走 disabled 发送
  - 预计文件：1–2 · 层：`minimal-chat.tsx` + `chat-composer.tsx`（`isSending` 显式 prop）

- [ ] 1.3 Web 单测或 storybook 快照：thinking 显示/隐藏条件
  - 预计文件：1 · 层：`apps/web/tests/unit/`（新建）

## 2. Story 9.1 — 安全（chat-security）

- [ ] 2.1 `CHAT_MAX_CONTENT_CHARS` + chat/demo-turn 长度校验
  - 预计文件：2 · 层：`core/config.py` + `services/security/content_validator.py`
  - Harness：`test_chat_security_contract.py`（超长 422）
  - **快失败**：不调 LLM 即 422；**北向** API 路由 / prepare，非 graph 节点

- [ ] 2.2 用户输入 Prompt 注入启发式 + `PROMPT_INJECTION_FILTER_ENABLED`
  - 预计文件：2 · 层：`services/security/prompt_security.py` + chat prepare 钩子
  - Harness：足球正例通过、override 短语 422
  - **EP13**：进 Remote Graph 前在 API 完成；不依赖子图进程

- [ ] 2.3 自研 `rag_sanitizer` 核心 + `ChunkSanitizer` 协议（Unicode、控制字符、override 短语、chunk 长度上限）
  - 预计文件：2 · 层：`services/security/rag_sanitizer.py` + `tests/unit/test_rag_sanitizer.py`
  - **无 FastAPI 依赖**；ETL / worker / EP13 子图可 import 同一模块
  - 不引入 npm `rag-poison-guard`（Node 栈）；EntropyShield 走 2.10 adapter 链，非硬依赖

- [ ] 2.4 retrieve 后接入 `rag_sanitizer`，再进 `build_rag_system_message`
  - 预计文件：2 · 层：`graphs/nodes/retrieve.py` + `prompts/rag_chat.py`（仅清洗调用点）
  - Unit：毒 chunk 不进 prompt 原文

- [ ] 2.5 World Cup ETL ingest 前调用同一 `rag_sanitizer`（纵深）
  - 预计文件：1–2 · 层：`scripts/etl/worldcup/` 入库路径
  - 验收：带注入短语的源文本入库后检索不到 raw override

- [ ] 2.6 分层 system prompt：`<POLICY>` + `<DOCS>` + `<TOOL_POLICY>`；用户 **仅** `HumanMessage`
  - 预计文件：2 · 层：`prompts/rag_chat.py` + `prompts/unified_react.py`
  - 禁止 system 内嵌 `<USER_QUERY>` 重复用户输入

- [x] 2.7 `docs/tech/chat-security.md` 威胁模型 + 策略对比 + 包试用指南
  - 预计文件：1 · 层：`docs/tech/chat-security.md`（已完成）
  - Harness：`test_chat_security_contract.py` 在 2.1–2.2 实现时补全

- [ ] 2.8 `UserInputGuard` 协议 + BFF `llm-prompt-guard` adapter（`BFF_PROMPT_GUARD_ENABLED`）
  - 预计文件：2 · 层：`apps/web/lib/prompt-guard.ts` + BFF chat route
  - 模式：`tag` 或 `quarantine`；API 仍为权威校验

- [ ] 2.9 LLM Guard adapter（`LLM_GUARD_ENABLED`）：`PromptInjection` + `InvisibleText`
  - 预计文件：2 · 层：`services/security/llm_guard_adapter.py` + chat prepare 钩子
  - Harness 默认关；benchmark 记录 p50 延迟

- [ ] 2.10 EntropyShield adapter（`ENTROPYSHIELD_ENABLED`）挂 `ChunkSanitizer` 链
  - 预计文件：2 · 层：`services/security/entropyshield_adapter.py` + retrieve 调用点
  - 验收：WC 足球正例误伤率可接受

- [ ] 2.11 `llm-injection-guard` 轻量中间件对照（`LLM_INJECTION_GUARD_ENABLED`）
  - 预计文件：2 · 层：`middleware/injection_guard.py` 或 deps
  - 与 2.2 自研规则对照实验，非默认热路径

- [ ] 2.12 Garak 红队脚本 + `docs/tech/chat-security.md` §7 试用结论回填
  - 预计文件：2 · 层：`scripts/security/garak_probe.sh` + docs 决策表
  - CI：nightly 非阻塞；Harness 正/反例仍为 PR 门禁

## 3. Story 9.4 — 限流与审计（rate-limit-audit）

> 设计：[`docs/tech/rate-limit-audit.md`](../../../docs/tech/rate-limit-audit.md)

- [ ] 3.1 Redis 滑动窗口 limiter 工具 + env 开关
  - 预计文件：2 · 层：`core/rate_limit.py` + `core/config.py`
  - Key：`rl:{route_class}:{user_id|ip}`；**多 API Pod 共享 Redis**（§12.3）

- [ ] 3.2 接入 login / chat completions / demo-turn 路由
  - 预计文件：2 · 层：`middleware/rate_limit.py` 或 router Depends
  - **仅北向 FastAPI**；Remote Graph 不对公网；Harness：超限 42901

- [ ] 3.3 Alembic `audit_log` 表 + 写入 demo-turn / login 失败
  - 预计文件：3 · 层：migration + `repositories/audit_repository.py` + demo-turn 钩子
  - Harness：demo-turn 后 audit 行存在
  - 敏感操作在 **API handler** 写入；EP13 internal 路由扩展留 metadata 字段

## 4. Story 9.3 — Token 与成本（token-usage）

- [ ] 4.1 Alembic `token_usage` 表 + repository
  - 预计文件：2 · 层：migration + `repositories/token_usage_repository.py`

- [ ] 4.2 `UsageRecorder` 协议 + `ChatService` finalize 写入；日聚合查配额
  - 预计文件：2 · 层：`services/token_quota_service.py` + `chat_service.py`（embedded recorder）
  - Harness：mock usage 落库；超配额 42902
  - **EP13**：remote 模式由 EP13 接 SSE usage 回传，复用同一 `UsageRecorder`（EP09 仅 protocol + embedded 实现）

- [ ] 4.3 `GET /api/v1/usage/me`（可选 FE 只读展示）
  - 预计文件：2 · 层：`api/v1/usage.py` + router
  - Harness：`test_usage_contract.py`

## 5. Story 9.2 — 性能（performance-cache）

- [ ] 5.1 Embedding Redis 缓存（hash key + TTL）
  - 预计文件：2 · 层：`embedding_service.py` + config
  - Unit：cache hit/miss

- [ ] 5.2 消息列表 / token 聚合索引 migration + 慢查询说明
  - 预计文件：2 · 层：Alembic + `docs/tech/performance.md`（新建短文）

- [ ] 5.3 Retrieve 耗时 structured log / trace span
  - 预计文件：1 · 层：`graphs/runner.py` 或 retrieve 节点

## 6. Story 9.8 L2 — Phase SSE（agent-phase-ui + chat-sse）

- [ ] 6.1 Runner 发 `phase` 事件（retrieve / model）；env 开关
  - 预计文件：2 · 层：`graphs/runner.py` + `chat_service.py`
  - Harness：`test_chat_phase_contract.py`（顺序断言）

- [ ] 6.2 BFF 映射 `phase` → AI SDK `data-agent-phase`
  - 预计文件：2 · 层：`memoryos-upstream.ts` + `sse-frames.ts`
  - Unit：`test_memoryos_data_stream.test.ts` 扩展

- [ ] 6.3 前端 `AgentPhaseIndicator` + chat-types 解析
  - 预计文件：3 · 层：新组件 + `chat-message-list.tsx` + `chat-types.ts`

## 7. Story 9.8 L3 — Tool pending polish

- [ ] 7.1 ToolTimeline：`tool_call` 无 result 时 pending 行
  - 预计文件：2 · 层：`tool-timeline.tsx` + `chat-store.ts`

- [ ] 7.2 可选折叠「思考过程」面板（prod 默认关）
  - 预计文件：2 · 层：`chat-message.tsx` + env flag

## 8. Story 9.5 — 降级（service-degradation）

- [ ] 8.1 LLM fallback model 路由 + 结构化 degrade log
  - 预计文件：2 · 层：`graphs/nodes/call_model.py` 或 runner
  - Unit：primary fail → fallback

- [ ] 8.2 Retrieve 超时 → 空 chunks 继续；Redis fail-open 文档对齐实现
  - 预计文件：2 · 层：retrieve 节点 + rate_limit fail-open 验证

## 9. Story 9.6 — 架构图

- [ ] 9.1 `docs/architecture/` 三张 Mermaid：系统总览、RAG、Agent
  - 预计文件：3 · 层：docs only
  - 系统总览含 **北向治理层**（422/429/audit）与 EP13 remote 执行层虚线框；链 [`rate-limit-audit.md` §12](../../../docs/tech/rate-limit-audit.md)

- [ ] 9.2 `docs/tasks/epics/EP09-optimization.md` 与 learning L07 勾选同步
  - 预计文件：2 · 层：epic + L07

## 10. Story 9.7 — LangSmith 生产策略

- [ ] 10.1 `LANGSMITH_SAMPLE_RATE` / `LANGSMITH_SAMPLE_ERRORS` config + runner 接入
  - 预计文件：2 · 层：`core/config.py` + tracing 初始化

- [ ] 10.2 `docs/tech/langsmith-production.md` 采样与免费额度说明
  - 预计文件：1 · 层：docs

## 11. Closeout

- [ ] 11.1 `pnpm test:api:harness` + web unit 全绿；epic 勾选
  - 预计文件：0 · 验证命令

- [ ] 11.2 OpenSpec archive `ep09-optimization`（全部 task 完成后）
  - 预计文件：openspec archive
