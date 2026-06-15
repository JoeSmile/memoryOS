# EP06 — 多层级记忆系统

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 7 周 |
| **优先级** | P1 |
| **依赖** | EP02、EP03 |
| **学习路线** | [L05-memory-workflow.md](../learning/L05-memory-workflow.md) |
| **目标文档** | [memory-system.md](../../tech/memory-system.md) · [ep06-memory-design.md](../../tech/ep06-memory-design.md) |

---

## Story 6.1 短期记忆

- [x] 滑动窗口 + 全局 Token 预算
- [x] tiktoken 计数与裁剪策略

## Story 6.2 长期记忆

- [x] `memories` 表 + 偏好/事实抽取
- [x] 用户画像摘要（会话级 `context_summary`）
- [x] LlamaIndex 长期记忆专属索引（`memories` 表 pgvector + `user_id` 过滤）

## Story 6.3 上下文压缩

- [x] 历史摘要合并（LLM）
- [x] 摘要 + 最近 N 轮混合策略

## Story 6.4 生命周期

- [x] 记忆更新、过期清理、用户手动删除

## Story 6.5 LangGraph 集成

- [x] 记忆读写节点嵌入对话 / Agent 图
- [x] 自动注入 system / 上下文

---

## MVP 后（企业级补强）

> 详见 [EP11 — 记忆运维](./EP11-memory-ops.md)、[EP12 — 记忆评测](./EP12-memory-eval.md)。

- [ ] 异步队列（摘要 / 抽取）— EP11
- [ ] 记忆溯源与 confidence — EP11
- [ ] 监控指标 — EP11
- [ ] 离线评测与回归 — EP12

---

## 同步学习

- [x] 上下文窗口限制与方案（理解 / 落地）
- [x] 对话摘要与压缩（理解 / 落地）
- [x] 长期记忆与画像（理解 / 落地）
- [x] 记忆与 Agent 联动（理解 / 落地）
