# EP12 — 记忆质量评测（MVP 后）

| 属性 | 值 |
|:-----|:---|
| **周期** | EP11 之后或并行（12 周计划外 backlog） |
| **优先级** | P2 |
| **依赖** | EP06 MVP、建议 EP11 Story 11.2（溯源字段便于评测归因） |
| **前置设计** | [`ep06-memory/design.md`](../../../openspec/changes/ep06-memory/design.md) · 企业级差距项 **评测** |
| **目标文档** | `docs/tech/memory-eval.md` 📋 |

> EP06 / EP09 不做 LLM-as-judge。本史诗建立 **记忆裁剪、摘要、抽取、检索注入** 的离线评测与回归门禁，避免改 prompt/阈值后 silently 退化。

---

## Story 12.1 评测数据集与基线

- [ ] 固定 fixture：短会话 / 50+ 轮长会话 / 含 ReAct tool 轮次 / 跨会话偏好场景
- [ ] 黄金数据：`expected_trim`（保留轮数下限）、`expected_memory_keys`、摘要应保留的约束句
- [ ] mock LLM 路径与真 LLM 路径分离（CI 默认 mock）
- [ ] 基线报告：当前 MVP 指标存档（trim 后 token、注入条数、摘要长度）

**验收**：`pnpm test:harness`（或等价）可跑 memory eval 套件且结果可复现。

---

## Story 12.2 摘要与裁剪回归

- [ ] 断言：超长历史 completion 不触发 provider context 错误（Harness 已有方向，扩展场景）
- [ ] 摘要质量：关键约束句召回（规则或 LLM judge 二选一，首版规则串匹配即可）
- [ ] 裁剪：ToolMessage 不被单独裁断导致 ReAct 断链（与 `short_term` 单测 + 场景用例）
- [ ] `SUMMARY_*` 节流参数变更时跑回归对比报告

**验收**：改 `MAX_CONTEXT_TOKENS` 或摘要 prompt 后，CI 能标红明显退化。

---

## Story 12.3 长期记忆抽取与检索评测

- [ ] 抽取：给定对话脚本，断言写入 `memories` 的类型与 key（mock 确定性路径）
- [ ] 检索：给定用户 query，断言 TopK 应包含 / 不应包含某条记忆（向量 fixture）
- [ ] 幻觉样本：不应写入的敏感/无关句 → 拒绝或低 confidence
- [ ] 可选：LLM-as-judge 批跑（仅 nightly，控制成本）

**验收**：抽取 prompt 或 embed 模型变更后，检索命中率指标可对比。

---

## Story 12.4 评测门禁与文档

- [ ] CI：memory eval 纳入 PR 可选 job（与现有 harness 并列）
- [ ] `docs/tech/memory-eval.md`：如何加场景、如何解读指标
- [ ] 与 LangSmith 数据集导出对齐（可选，便于人工 spot check）

**验收**：README / work-next 流程中注明「改 memory 模块须跑 eval 套件」。

---

## 与 EP09 / EP10 的边界

| 史诗 | 边界 |
|:-----|:-----|
| EP09 | 全站性能、安全、Token 成本；Story 9.8 Agent phase UI |
| EP10 | 面试素材、产品 polish；Story 10.6 记忆确认 UI |
| **EP12** | **仅记忆子系统质量**：裁剪、摘要、抽取、检索注入 |

---

## 同步学习

- [ ] Agent 记忆离线评测方法论（理解 / 落地）
- [ ] LLM-as-judge 成本与偏差（理解）
- [ ] 回归测试 vs 探索性评测（理解）
