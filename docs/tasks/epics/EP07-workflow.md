# EP07 — AI 可视化工作流引擎（已砍掉）

| 属性 | 值 |
|:-----|:---|
| **原计划周期** | 第 7 周 |
| **优先级** | P2 |
| **状态** | **⏸ 已砍掉，不实施** |
| **原因** | 优先 EP08 本地 Docker 全栈；工作流与 `/chat` 能力重叠度高；编排能力延后至 MVP 后 |

---

## 原目标（归档）

- 独立 LangGraph 工作流 + `workflow_runs` 持久化
- 世界杯 `match-analysis` Demo（`wc_*` + RAG → 报告）
- 前端步骤条；显式 API 触发（非 Cron / 非 chat 关键字）

设计草案曾写入 git 历史 commit `130b6bb`（`openspec/changes/ep07-workflow/`，已自工作区移除）。

---

## MVP 后若恢复

| 方向 | 参考 |
|:-----|:-----|
| 持久队列、Cron、run SSE | [EP11 — 记忆运维](./EP11-memory-ops.md) |
| Remote Graph / 多 Worker | [EP13 — 分布式](./EP13-memory-distributed.md) |
| 工作流 UI / `langgraph.json` | [post-mvp-roadmap.md](../post-mvp-roadmap.md) |

---

## Story 勾选（全部不适用）

- [ ] ~~7.1–7.4~~ — 未实施

## 同步学习

- [ ] ~~L05 Part B~~ — 见 [L05-memory-workflow.md](../learning/L05-memory-workflow.md)（Part A 记忆仍有效）
