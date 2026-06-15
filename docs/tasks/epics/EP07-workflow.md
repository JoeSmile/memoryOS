# EP07 — AI 可视化工作流引擎

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 7 周 |
| **优先级** | P2（可延后） |
| **依赖** | EP04（RAG + `wc_*`）、EP05 |
| **学习路线** | [L05-memory-workflow.md](../learning/L05-memory-workflow.md) |
| **OpenSpec** | [ep07-workflow](../../openspec/changes/ep07-workflow/design.md)（与本文互链） |
| **MVP 后** | Remote Graph / `langgraph.json` 与 [EP13](./EP13-memory-distributed.md) 对齐；异步队列优先 [EP11](./EP11-memory-ops.md) |

---

## 本史诗要解决的问题

EP02–EP06 已具备 **世界杯 RAG 流式对话 / ReAct / 记忆**，但缺少：

- **结构化多步编排**（固定 pipeline，而非每轮自由对话）
- **run 级可观测性**（步骤、日志、异步状态、历史报告）

EP07 用 **与产品同域** 的 Demo——**选一场 `wc_*` 比赛 → 拉 Silver 事实 + RAG → 生成对阵分析报告**——证明「业务工作流 = 独立 LangGraph + 持久化 run」，并与 `/chat` **互补**（见下表）。

**刻意不做**：简历/JD、PDF 解析、运行时 CSV 上传、拖拽画布、Cron 批处理、chat 关键字触发。

---

## 与 `/chat` 的产品分工

| | `/chat` | `/workflows/match-analysis` |
|:--|:--------|:----------------------------|
| **目的** | 自由问答、追问、Agent | 固定模板、一次跑完、可回看 |
| **交互** | SSE 流式 | 选场次 + 按钮 → REST 轮询 + 步骤条 |
| **输入** | 用户自然语言 | `match_id`（DB）+ 可选 `analysis_focus` |
| **数据** | RAG + 记忆 + messages | **`wc_*` 结构化事实** + RAG chunks |
| **编排** | `chat_graph`（trim → memory → retrieve → ReAct） | `graphs/workflows/match_analysis_graph` |
| **输出** | 对话气泡 | `result_json.report` + step 日志 |

Chat 里 **不** 用 magic word 触发 workflow；首版 **不** 改 chat SSE。日后若从 chat 跳转，应 **调同一 POST runs API**（深链/按钮），而非解析关键字。

---

## 如何触发（Trigger）

| 方式 | EP07 MVP | 说明 |
|:-----|:---------|:-----|
| **前端按钮 + API** | ✅ 采用 | `/workflows/match-analysis` 选场次 →「开始分析」→ `POST /api/v1/workflows/match-analysis/runs` |
| **轮询结果** | ✅ | `GET /api/v1/workflow-runs/{id}` 更新步骤条与报告 |
| **BackgroundTasks** | ✅ | HTTP 响应后异步跑 LangGraph（同 EP06 摘要/记忆） |
| **Cron / 定时批处理** | ❌ | 适合 EP11+ 队列；非本史诗 Demo |
| **Chat 关键字** | ❌ | 易与 ReAct/RAG 边界混淆；独立页为主入口 |

```text
用户点「开始分析」
  → POST .../runs { match_id, analysis_focus? }
  → 写入 workflow_runs + steps
  → BackgroundTasks 执行 match_analysis_graph
  → 前端轮询 GET /workflow-runs/{id}
```

---

## 分析怎么做（不是完全交给 LLM）

编排规则在 **代码定义的 LangGraph 节点**里（首版非用户可配规则引擎）。LLM **仅最后一步**写报告；事实以 DB + RAG 为准。

### 输入含义

| 字段 | 作用阶段 | 含义 |
|:-----|:---------|:-----|
| **`match_id`** | 节点 ①–③ | 锁定 **哪一场**；从 `wc_matches` 及关联表拉比分、阶段、进球、红黄牌、球队统计等 **可核对事实** |
| **`analysis_focus`**（可选） | 节点 ③–④ | 如「边路进攻」「点球大战」——**不改 SQL**；影响 **RAG query 措辞** 与 **报告 prompt 写作角度** |

### 线性 pipeline（`workflow_slug=match-analysis`）

```text
validate_match          校验 match_id 存在于 wc_matches
load_match_context      SQL 组装 match_facts（确定性，不用 LLM）
retrieve_match_knowledge  用 facts + focus 拼 query → KnowledgeSearchService TopK
generate_report         LLM：基于 facts + chunks 写报告；prompt 禁止编造比分/统计
finalize_output         写入 run.result_json.report
```

### 举例：决赛 + focus「边路进攻」

1. **`match_id`**：拉出该场比分、进球者、加时/点球等 Silver 数据（与 focus 无关，基础材料相同）。
2. **`analysis_focus`**：RAG 检索偏向边路/宽度相关 fact_cards；报告要求专节写边路，**若无数据则声明不足、勿虚构**（如没有传球热点就不写「左路占比 62%」）。
3. **LLM**：综合叙述与组织结构，**不**从 raw CSV 心算 xG 或战术统计。

首版 **不** 做：计算机视觉、按 focus 动态改 SQL 子集（可作为后续增强：如 focus=点球 → 只组装 `wc_penalty_kicks`）。

---

## Story 7.1 引擎架构

- [ ] 节点类型：Input、LLM、Tool（DB/RAG）、Output（Condition 首版不做）
- [ ] 线性 workflow + `workflow_runs` / `workflow_run_steps` 状态
- [ ] 异步 `BackgroundTasks`（生产队列见 **EP11**；Worker 见 **EP13**）

## Story 7.2 世界杯对阵分析 Demo

- [ ] 从 **`wc_matches`（EP04-01 ETL / CSV→DB）** 选择场次（`GET .../match-analysis/matches`）
- [ ] 加载 Silver 事实 + RAG 检索 → LLM  grounded 报告
- [ ] **不做** 简历/JD/PDF/运行时 CSV 上传

## Story 7.3 可视化

- [ ] 场次下拉 + 可选 focus + 步骤条、节点日志
- [ ] 历史 run 列表与查看；ChatHeader 链到 `/workflows/match-analysis`

## Story 7.4 LangGraph 规范

- [ ] 独立 `graphs/workflows/` 图；与 `chat_graph` 并列，避免两套编排标准

---

## MVP 后（不在 EP07 范围）

| 能力 | 史诗 |
|:-----|:-----|
| 持久队列、Cron 批分析、run SSE | EP11 |
| Remote Graph / `langgraph.json` | EP13 |
| Chat 内「生成完整报告」按钮（仍调 runs API） | EP09/EP10 可选 |
| focus → 代码级 facts 子集（如点球专用 SQL） | 后续 change |

---

## 同步学习

- [ ] AI 业务流程编排（理解 / 落地）
- [ ] 轻量任务队列（理解 / 落地）
- [ ] 同域工作流 vs 自由对话（理解）
