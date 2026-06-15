## Context

- **现状**：`wc_*` Silver 表（EP04-01 ETL）+ RAG `KnowledgeSearchService`（EP04 chat）；`chat_graph` 为自由对话；`BackgroundTasks` 已用于 EP06。
- **约束**：工作流 **REST 轮询**，不改 chat SSE；**只读**世界杯 DB + RAG，不写知识库。
- **依赖**：EP03 JWT、EP04-01 `wc_matches`、EP04 RAG、EP05 LLM/mock、EP06 异步惯例。
- **产品决策**：Demo **对齐世界杯主域**；输入为 **`match_id`（来自 DB）** + 可选 **`analysis_focus`**；**非**简历/PDF/Cron/chat 关键字触发。
- **史诗对齐**：[`docs/tasks/epics/EP07-workflow.md`](../../docs/tasks/epics/EP07-workflow.md)

## Goals / Non-Goals

**Goals:**

- 聊天之外第二条路径：**选场次 → 多步 pipeline → 结构化报告**（固定模板、可回看 run）。
- 复用 **Silver 表事实 + RAG chunks**；**LLM 仅最后一步**写报告，事实以 DB + RAG 为准（grounded）。
- **用户显式触发**：前端按钮 → `POST .../runs` → `BackgroundTasks` → 轮询步骤条。
- Harness 用固定 `match_id` mock 确定性。

**Non-Goals:**

- 简历/JD/PDF/运行时 CSV 上传、拖拽画布、Condition 分支
- **Cron / 定时批分析**（→ EP11 队列）
- **Chat 关键字 / magic word** 触发 workflow（独立页为主；日后 chat 仅深链调同一 API）
- 用户可配规则引擎、动态 DAG 编译（首版 slug → 预编译 LangGraph）
- 新 ETL、pgvector 写入、生产队列 → EP11、Remote Graph → EP13

## 与 `/chat` 的产品分工

| | `/chat` | `/workflows/match-analysis` |
|:--|:--------|:----------------------------|
| **目的** | 自由问答、追问、Agent | 固定模板、一次跑完、可回看 |
| **交互** | SSE 流式 | 选场次 + 按钮 → REST 轮询 + 步骤条 |
| **输入** | 用户自然语言 | `match_id`（DB）+ 可选 `analysis_focus` |
| **数据** | RAG + 记忆 + messages | **`wc_*` 结构化事实** + RAG chunks |
| **编排** | `chat_graph` | `graphs/workflows/match_analysis_graph` |
| **输出** | 对话气泡 | `result_json.report` + step 日志 |

## Decisions

### D1: LangGraph 独立模块，chat 图不动

**选择**：`graphs/workflows/match_analysis_graph.py` + `WorkflowRunState`（非 `ChatState`）。  
**理由**：Story 7.4 — 同一 LangGraph **模式**，不同业务图；避免 `chat_service` 分支爆炸。

### D2: 首版线性五步（世界杯）

编排规则在 **代码节点**里（非用户可配规则引擎）：

```text
validate_match → load_match_context → retrieve_match_knowledge → generate_report → finalize_output
```

| 类型 | 节点 | LLM? | 说明 |
|:-----|:-----|:----|:-----|
| Input | `validate_match` | 否 | 校验 `match_id` ∈ `wc_matches` |
| Tool/DB | `load_match_context` | 否 | SQL 组装 match_facts：比分、阶段、进球、红黄牌、`wc_team_match_stats` 等 |
| RAG | `retrieve_match_knowledge` | 否 | facts + `analysis_focus` 拼 query → `KnowledgeSearchService` TopK |
| LLM | `generate_report` | **是** | 基于 facts + chunks 写报告；prompt **禁止编造**比分/统计 |
| Output | `finalize_output` | 否 | 写 `run.result_json.report` |

首版 **无** Condition；Tool 指 DB/RAG 服务调用，非 ReAct 循环。

### D3: 输入字段语义

| 字段 | 作用阶段 | 含义 |
|:-----|:---------|:-----|
| **`match_id`** | ①–③ | 锁定 **哪一场**；从 `wc_*` 拉 **可核对事实**（与 focus 无关的基础材料） |
| **`analysis_focus`**（可选，默认「战术要点」） | ③–④ | **不改 SQL**；影响 RAG query 措辞 + 报告 prompt **写作角度** |

**举例（决赛 + focus「边路进攻」）**：

1. `match_id` → 拉出比分、进球者、加时/点球等 Silver 数据。
2. `analysis_focus` → RAG 偏向边路/宽度相关 chunks；报告专节写边路；**无数据则声明不足、勿虚构**（如无传球热点则不写「左路占比 62%」）。
3. LLM → 综合叙述；**不**从 raw CSV 心算 xG。

首版 **不** 做：按 focus 动态改 SQL 子集（后续可增强，如 focus=点球 → 只组装 `wc_penalty_kicks`）。

**列表 API**：`GET .../matches` 查 `wc_*`（featured / `tournament_id` 过滤）；非用户上传 CSV。

### D4: Run 持久化

- `workflow_runs`：`workflow_slug=match-analysis`，`input_json={ match_id, analysis_focus? }`，`result_json.report`
- `workflow_run_steps`：与 D2 `step_key` 一一对应

### D5: Trigger（如何启动）

| 方式 | EP07 | 说明 |
|:-----|:-----|:-----|
| 前端「开始分析」+ `POST .../runs` | ✅ | 主路径 |
| `GET /workflow-runs/{id}` 轮询 | ✅ | 步骤条 + 报告 |
| `BackgroundTasks` | ✅ | HTTP 响应后跑图（同 EP06） |
| Cron / 批处理 | ❌ | EP11+ |
| Chat 关键字 | ❌ | 易与 ReAct 混淆 |

```text
用户点「开始分析」
  → POST .../runs { match_id, analysis_focus? }
  → INSERT workflow_runs + steps
  → BackgroundTasks: run_match_analysis_graph
  → 前端轮询 GET /workflow-runs/{id}
```

### D6: HTTP API

| 方法 | 路径 |
|:-----|:-----|
| GET | `/api/v1/workflows/match-analysis/matches` |
| POST | `/api/v1/workflows/match-analysis/runs` |
| GET | `/api/v1/workflow-runs/{id}` |
| GET | `/api/v1/workflow-runs?workflow_slug=match-analysis` |

跨用户 GET → 404 `workflow_run_not_found`。

### D7: RAG 与 chat 边界

- **相同**：`KnowledgeSearchService`、collection、top_k / min_score（可 `WORKFLOW_RAG_*` 别名）。
- **不同**：query 由 **match context + focus** 生成；结果进 `WorkflowRunState`，不进 `ChatState.messages`。
- **不写**：memories、conversations。

### D8: 前端（Story 7.3）

- `/workflows/match-analysis`：场次下拉 + 可选 focus + **「开始分析」按钮**
- 步骤条 + 节点日志 + 报告；最近 run 列表；ChatHeader 链入
- **无**拖拽画布

### D9: 功能开关

| 变量 | 默认 | 说明 |
|:-----|:-----|:-----|
| `WORKFLOW_ENABLED` | true | 总开关 |
| `WORKFLOW_MATCH_ANALYSIS_ENABLED` | true | Demo 路由 |
| `WORKFLOW_DEFAULT_TOURNAMENT_ID` | `WC-2022` | matches 列表默认赛事 |

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| 本地无 ETL 数据 | Harness fixture / 文档要求 ETL |
| RAG 无命中 | 仍可用 Silver facts；step 标注 rag_empty |
| 与 chat 重叠 | 工作流=固定报告；chat=追问 |
| LLM 编造统计 | generate_report prompt 约束 + facts 前置 |

## Migration Plan

1. Alembic：`workflow_runs` + `workflow_run_steps`
2. 部署 API + web（依赖 `wc_*` + RAG ingest）
3. 回滚：`WORKFLOW_ENABLED=false`

## Open Questions

- [x] Trigger：用户显式 API，非 Cron/chat 关键字（见 D5）
- [ ] `featured` 硬编码 5–10 场 + 可选 `tournament_id` 过滤

## MVP 后

| 能力 | 史诗 |
|:-----|:-----|
| 持久队列、Cron、run SSE | EP11 |
| Remote Graph | EP13 |
| Chat 内按钮调同一 runs API | EP09/EP10 |
| focus → SQL 子集 | 后续 change |

见 [post-mvp-roadmap.md](../../docs/tasks/post-mvp-roadmap.md) · [EP07-workflow.md](../../docs/tasks/epics/EP07-workflow.md)。
