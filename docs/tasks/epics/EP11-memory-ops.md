# EP11 — 记忆系统运维补强（MVP 后）

| 属性 | 值 |
|:-----|:---|
| **周期** | EP06 MVP 上线后（12 周计划外 backlog） |
| **优先级** | P2 |
| **依赖** | EP06（`ep06-memory` MVP）、EP08 部署基线 |
| **前置设计** | [`ep06-memory/design.md`](../../../openspec/changes/ep06-memory/design.md) · 企业级差距项 **队列 + 溯源 + 监控** |
| **目标文档** | `docs/tech/memory-system.md`（§ 生产运维）📋 |

> EP06 首版用 `BackgroundTasks` 做摘要/抽取、无记忆溯源字段、监控主要靠 LangSmith。本史诗把记忆子系统补到 **可长期多实例运行、可排障、可解释**。

---

## Story 11.1 异步任务队列（摘要 + 记忆抽取）

**背景**：`BackgroundTasks` 在进程重启、多 Worker、部署滚动时可能丢任务；无重试与死信。

- [ ] 选型：ARQ / Celery / 云队列（与 EP08 基础设施对齐）
- [ ] 任务类型：`schedule_summary`、`extract_memories`；幂等键（`conversation_id` + 回合 `message_id`）
- [ ] 重试策略、最大重试、死信或失败表 + 告警钩子
- [ ] 与 `should_schedule_summary` / finalize 钩子对接（提交任务而非 inline BackgroundTasks）
- [ ] Harness：mock worker 跑一轮摘要/抽取契约
- [ ] 回滚：`MEMORY_USE_BACKGROUND_TASKS=true` 开关保留旧路径

**验收**：API 滚动部署后，已 finalize 的会话仍能在 SLA 内（如 5min）完成摘要或进入失败可查询状态。

---

## Story 11.2 记忆溯源与质量元数据

**背景**：长期记忆无法回答「从哪条对话来的」；抽取幻觉难追责；key upsert 无法处理矛盾事实。

- [ ] `memories` 扩展（或关联表）：`source_conversation_id`、`source_message_id`、`extracted_at`、`confidence`（0–1）
- [ ] 抽取 prompt 输出 confidence；低于阈值不入库或标 `pending`
- [ ] 同 `key` 冲突策略文档化：高 confidence 覆盖 / 保留两条 + `superseded_by`（首版二选一）
- [ ] `GET /memories` 返回溯源字段（不含 embedding）；前端 `/memories` 可选展示来源会话
- [ ] 用户注销 / 删会话时级联策略（软删记忆或清溯源）
- [ ] Harness：抽取结果带溯源字段契约

**验收**：任意一条 memory 可追溯到会话与消息；用户删记忆与删会话行为符合产品说明。

---

## Story 11.3 记忆子系统监控指标

**背景**：`trim_stats` 不进 SSE；生产需 metrics 看裁剪率、摘要滞后、抽取失败。

- [ ] 指标（建议 Prometheus 或结构化日志 + 后续接入）：
  - `memory_trim_dropped_turns`、`memory_trim_token_count`
  - `summary_scheduled` / `summary_success` / `summary_latency_ms`
  - `memory_extract_success` / `memory_extract_failure`
  - `memory_inject_count`（每轮注入条数）
- [ ] 与 LangSmith trace 关联 id（`conversation_id` / `stream_id`）
- [ ] 告警建议：摘要失败率、抽取失败率、队列积压（Story 11.1 后）
- [ ] `docs/tech/memory-system.md` 运维章节

**验收**：dev/staging 可查到一次 completion 的 trim 与 inject 指标；失败任务可在日志或面板定位。

---

## 与 EP06 Non-Goals 的对应

| EP06 明确不做 | EP11 承接 |
|:--------------|:----------|
| Celery/ARQ 队列 | Story 11.1 |
| 抽取用户确认 UI | Story 11.2 为数据基础；确认 UI 可 EP10 Story 10.6 |
| `trim_stats` 不进 SSE | Story 11.3 走 metrics |

---

## 同步学习

- [ ] 异步任务与至少一次投递（理解 / 落地）
- [ ] 记忆溯源与 GDPR 删除联动（理解）
- [ ] Agent 系统可观测性指标设计（理解 / 落地）
