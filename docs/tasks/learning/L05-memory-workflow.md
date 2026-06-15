# L05 — 记忆 + 工作流（第 7 周）

**对应史诗**：[EP06](../epics/EP06-memory.md)（P1，**已落地**）+ [EP07](../epics/EP07-workflow.md)（P2，进行中）

| Part | 史诗 | 状态 | 权威文档 |
|:-----|:-----|:-----|:---------|
| A 记忆 | EP06 | ✅ | [memory-system.md](../../tech/memory-system.md) · [ep06-memory-design.md](../../tech/ep06-memory-design.md) |
| B 工作流 | EP07 | 📋 | [openspec ep07-workflow](../../openspec/changes/ep07-workflow/design.md) · `workflow-engine.md`（task 6.1 待写） |

---

# Part A — 记忆系统（EP06）

## 1. 上下文与 Token 预算

### 学什么

- [x] 📖 模型 context window；input + output 合计限制
- [x] 📖 tiktoken 按模型计数；中英混合差异
- [x] 📖 预算分配：system + 记忆 + RAG + 历史 + 用户输入
- [x] 🔧 `MAX_CONTEXT_TOKENS`、`RESERVE_FOR_REPLY`（`config.py`）

### 面试常问

- 上下文满了怎么办？业界有哪些方案？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 只数字符不数 token | 仍超限 API 报错 | 统一 `token_counter` |
| 未给回复留预算 | 生成被截断 | `RESERVE_FOR_REPLY` |

---

## 2. 短期记忆（滑动窗口）

### 学什么

- [x] 📖 保留最近 N 轮 / M tokens；从最旧 turn 删起
- [x] 📖 DB 全量 messages ≠ 进 LLM 的全量（裁剪仅图内）
- [x] 📖 `trim_history` 只裁 `messages`；`context_summary` 只参与 token 预算
- [x] 🔧 `services/memory/short_term.py` + `graphs/nodes/trim_history.py`

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 裁剪把 system 裁掉 | 人设丢失 | system / 注入块永不裁 |
| UI 与模型所见不一致 | 用户以为「忘了」 | Header 提示「后端裁剪」 |

---

## 3. 长期记忆

### 学什么

- [x] 📖 finalize 后异步抽取：preference / fact / constraint
- [x] 📖 `memories` 表 + pgvector；TopK 按 `user_id` 过滤
- [x] 📖 与 RAG 世界杯知识库 **读写分离**
- [x] 📖 同 `memory_key` upsert 覆盖；用户可删
- [x] 🔧 `long_term.py` + `load_user_memories` + 前端 `/memories`

### 面试常问

- 长期记忆和 RAG 知识库区别？会不会互相污染？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 抽取幻觉当事实 | 错误人设 | 用户删除 + prune |
| 记忆无限增长 | 检索噪声 | `expires_at` + importance 阈值 |

---

## 4. 会话摘要（中期记忆）

### 学什么

- [x] 📖 `conversations.context_summary`；rolling 合并
- [x] 📖 节流：首次 `SUMMARY_TRIGGER_TOKENS`；后续 increment + cooldown
- [x] 📖 摘要 **下一轮** 才注入；`BackgroundTasks` 不阻塞 SSE
- [x] 🔧 `summary_service.py` + `chat_service` finalize 调度

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 摘要丢关键约束 | 后续违反用户要求 | rolling prompt 强调约束 |
| 每轮都跑 summary | 成本爆炸 | increment + cooldown |

---

## 5. LangGraph 记忆节点（对话图）

- [x] 📖 拓扑：`trim_history` → `load_user_memories` → `retrieve` → `call_model` (± tools)
- [x] 📖 finalize 后并行：summary + memory extract
- [x] 🔧 详见 [ep06-memory-design.md §8 Walkthrough](../../tech/ep06-memory-design.md)

### MVP 后

- [ ] 持久队列、溯源、监控 → [EP11](../epics/EP11-memory-ops.md)
- [ ] 离线评测回归 → [EP12](../epics/EP12-memory-eval.md)

---

# Part B — 工作流（EP07，可选）

> 史诗说明（Trigger、分析模型、与 chat 分工）：[EP07-workflow.md](../epics/EP07-workflow.md) · OpenSpec：[design.md](../../openspec/changes/ep07-workflow/design.md)  
> Remote Graph → [L09](./L09-distributed-orchestration.md) / [EP13](../epics/EP13-memory-distributed.md)；生产队列 → [EP11](../epics/EP11-memory-ops.md)。

## 1. 编排概念

### 学什么

- [ ] 📖 DAG vs 状态机；本项用 LangGraph 状态机
- [ ] 📖 独立图 `graphs/workflows/`，与 `chat_graph` 并列
- [ ] 📖 **Trigger**：前端按钮 → POST runs → BackgroundTasks → 轮询（**非** Cron、**非** chat 关键字）
- [ ] 📖 异步 run 状态落 `workflow_runs` / `workflow_run_steps`

### 与 /chat 分工

| | `/chat` | `/workflows/match-analysis` |
|:--|:--------|:----------------------------|
| 目的 | 自由问答、Agent | 固定报告、可回看 run |
| 交互 | SSE 流式 | 按钮 + REST 轮询 + 步骤条 |
| 输入 | 自然语言 | `match_id` + 可选 `analysis_focus` |
| 数据 | RAG + 记忆 | `wc_*` 事实 + RAG |
| LLM | 多轮对话/ReAct | ** mainly 最后一步写报告** |

---

## 2. 世界杯对阵分析 Demo

### 学什么

- [ ] 📖 输入：`wc_matches.match_id`（EP04-01 CSV→ETL→DB）；非 PDF / 非简历
- [ ] 📖 **非全 LLM**：SQL 装 facts → RAG 检索 → LLM grounded 写报告
- [ ] 📖 `analysis_focus`（如「边路进攻」）**不改 SQL**；影响 RAG query + 报告角度；无数据则声明不足
- [ ] 🔧 `GET .../matches` + `POST .../runs` + `GET /workflow-runs/{id}`
- [ ] 🔧 `/workflows/match-analysis`（下拉 + focus +「开始分析」）

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 与 chat 混一套图 | 维护成本高 | 独立 `match_analysis_graph` |
| 以为 focus 会算战术统计 | LLM 编造占比 | facts 前置 + prompt 禁止幻觉 |
| 长任务无持久状态 | 刷新丢进度 | `workflow_runs` + 轮询 |
| 本地无 `wc_*` 数据 | run 失败 | migration + ETL 或 Harness fixture |

---

## 3. LangGraph 规范（Story 7.4）

- [ ] 📖 工作流节点类型：Input、LLM、Tool（DB/RAG）、Output
- [ ] 📖 首版 **不做** Condition 分支、拖拽画布
- [ ] 🔧 OpenSpec：[ep07-workflow/tasks.md](../../openspec/changes/ep07-workflow/tasks.md)

---

## 阶段自测

**EP06（应能口述）**

- [ ] 短期 + 摘要 + 长期 如何同时进 prompt、`trim_history` 与摘要的关系
- [ ] 3 个记忆踩坑 + 对策（裁剪、摘要滞后、RAG 与记忆隔离）

**EP07（落地后）**

- [ ] 工作流 **如何触发**（按钮 + API，非 Cron/chat 关键字）
- [ ] `match_id` vs `analysis_focus`；为何 **不是全 LLM**
- [ ] Demo 录屏 ~2 分钟：选场次 → 步骤条 → 报告
