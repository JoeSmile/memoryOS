## Why

EP02–EP06 已具备 **世界杯 RAG 流式对话 / ReAct / 记忆**，但缺少 **结构化多步编排** 与 **run 级可观测性**。EP07 用 **同域 Demo**——从 `wc_*` 选一场对阵 → Silver 事实 + RAG → **grounded** 分析报告——证明「工作流 = 独立 LangGraph + 持久化 run」，与 `/chat` **互补**（自由问答 vs 固定 pipeline），并为 EP11/EP13 留接口。

## What Changes

- **工作流引擎**：代码定义 LangGraph；`workflow_runs` + `workflow_run_steps`。
- **世界杯对阵分析**：`match_id`（DB）+ 可选 `analysis_focus` → 五步 pipeline；**LLM 仅最后一步**写报告。
- **Trigger**：用户在前端点「开始分析」→ `POST .../runs` → `BackgroundTasks` → 轮询（**非** Cron、**非** chat 关键字）。
- **HTTP API**：`GET .../matches` · `POST .../runs` · `GET /workflow-runs/{id}` · list。
- **前端**：`/workflows/match-analysis`（场次下拉、focus、步骤条、报告）。
- **Harness** + **`docs/tech/workflow-engine.md`** + 史诗 [`EP07-workflow.md`](../../docs/tasks/epics/EP07-workflow.md) 叙事对齐。

**Non-Goals（本 change 不做）：**

- 简历/JD/PDF/运行时 CSV 上传、拖拽画布、Condition 分支、用户自定义 DAG
- **Cron / 定时批分析**、**chat magic word 触发**
- 新 ETL、改 chat SSE、Celery（→ EP11）、Remote Graph（→ EP13）、Playwright E2E

## Capabilities

### New Capabilities

- `workflow-engine`: run 持久化、match-analysis LangGraph、显式 API 触发、grounded 报告、步骤日志

### Modified Capabilities

- `core-schema`: `workflow_runs`、`workflow_run_steps`

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/app/graphs/workflows/` | `match_analysis_graph.py`、`WorkflowRunState`、prompts |
| `apps/api/app/repositories/` | workflow + `wc_match` 只读查询 |
| `apps/api/app/services/workflow/` | run_service、BackgroundTasks |
| `apps/api/app/services/knowledge_search_service.py` | 工作流 RAG 节点（只读） |
| `apps/api/app/api/v1/workflows.py` | matches / runs / poll |
| `apps/web/` | `/workflows/match-analysis` |
| `docs/tech/workflow-engine.md` | 触发、分析模型、与 chat 边界 |
| `docs/tasks/epics/EP07-workflow.md` | 史诗说明（与 design 互链） |
