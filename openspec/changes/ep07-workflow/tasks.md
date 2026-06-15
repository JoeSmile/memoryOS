## 0. Human review（apply 前必过）

> propose 完成后 **必须停在这里**等人审；未勾选前 **禁止**写业务代码。

- [ ] **Tasks reviewed by human** — 人审通过后再 `/opsx:apply`、`/work-next` 或说「继续实现」

### Review checklist

- [x] 前后端成对：`GET matches` + `POST/GET workflow-runs` ↔ `/workflows/match-analysis` +「开始分析」按钮 + 导航
- [x] **Trigger**：显式 POST + BackgroundTasks + 轮询；**无** Cron、**无** chat 关键字
- [x] **分析模型**：load/RAG 不用 LLM；`analysis_focus` 只影响 query/prompt；报告 grounded
- [x] **世界杯同域**：`wc_matches.match_id`（DB/ETL）；**无**简历/PDF/CSV 上传
- [x] Harness：固定 `match_id`、步骤顺序、跨用户 404
- [x] 与 [`EP07-workflow.md`](../../docs/tasks/epics/EP07-workflow.md) 叙事一致
- [x] 每条 task ≤3 文件 / ~150 行

**Reviewer notes:**（可选）

**Trigger + 数据流：**

```text
GET .../match-analysis/matches  ← wc_* 只读
用户点「开始分析」
  → POST .../runs { match_id, analysis_focus? }
  → workflow_runs + steps
  → BackgroundTasks: match_analysis_graph
       validate → load_match_context (SQL)
       → retrieve_match_knowledge (RAG, query 含 focus)
       → generate_report (LLM, grounded)
       → finalize_output
  → GET /workflow-runs/{id} 轮询步骤条 + 报告
```

---

## 1. Config

- [ ] 1.1 `WORKFLOW_ENABLED`、`WORKFLOW_MATCH_ANALYSIS_ENABLED`、`WORKFLOW_DEFAULT_TOURNAMENT_ID` in `config.py` + `.env.example`
  - 预计文件：2 · 层：`apps/api/app/core/config.py` + `.env.example`

## 2. Schema & repository（Story 7.1）

- [ ] 2.1 Alembic：`workflow_runs` + `workflow_run_steps`；更新 `docs/database.md`
  - 预计文件：2 · 层：`alembic/versions/` + `docs/database.md`

- [ ] 2.2 `WorkflowRun` / `WorkflowRunStep` ORM + `workflow_run_repository` + Pydantic schemas
  - 预计文件：3 · 层：`models/workflow_run.py` + `repositories/workflow_run_repository.py` + `schemas/workflow.py`

- [ ] 2.3 `WcMatchRead` 查询：`list_matches_for_workflow()`（join teams，featured/tournament 过滤）
  - 预计文件：2 · 层：`repositories/worldcup/match_repository.py` + `schemas/worldcup_match.py`

## 3. LangGraph match-analysis（Story 7.2 + 7.4）

- [ ] 3.1 `WorkflowRunState` + prompts（`match_analysis.py`）— grounded 报告、`analysis_focus` 进 RAG query + report system
  - 预计文件：2 · 层：`graphs/workflows/state.py` + `graphs/workflows/prompts/match_analysis.py`

- [ ] 3.2 `match_analysis_graph.py` — 五节点线性链（validate → load → retrieve → generate → finalize）
  - 预计文件：2 · 层：`graphs/workflows/match_analysis_graph.py` + `tests/unit/test_match_analysis_graph.py`

- [ ] 3.3 `workflow/run_service.py` — 创建 run/steps、BackgroundTasks、step 状态更新
  - 预计文件：2 · 层：`services/workflow/run_service.py` + `tests/unit/test_workflow_run_service.py`

## 4. Workflow HTTP API

- [ ] 4.1 `GET .../match-analysis/matches` + `POST .../match-analysis/runs` + `GET /workflow-runs/{id}` + list + router
  - 预计文件：3 · 层：`api/v1/workflows.py` + `services/workflow_service.py` + `router.py`

- [ ] 4.2 Harness `test_workflow_run_contract.py` — 种子/固定 match_id、mock LLM、步骤顺序、404 TDD 先写
  - 预计文件：1 · 层：`tests/harness/test_workflow_run_contract.py`

## 5. 前端可视化（Story 7.3）

- [ ] 5.1 `lib/api-client.ts` workflow 方法 + `lib/workflow-types.ts`
  - 预计文件：2 · 层：`apps/web/lib/api-client.ts` + `lib/workflow-types.ts`

- [ ] 5.2 `/workflows/match-analysis` — 场次下拉、可选 focus、「开始分析」按钮、轮询、步骤条 + 日志 + 报告
  - 预计文件：2 · 层：`app/workflows/match-analysis/page.tsx` + `components/workflows/match-analysis-panel.tsx`

- [ ] 5.3 导航入口链到 `/workflows/match-analysis`；最近 run 列表
  - 预计文件：1–2 · 层：`components/chat/chat-header.tsx`

## 6. Docs & closeout

- [ ] 6.1 `docs/tech/workflow-engine.md` — Trigger、分析模型（非全 LLM）、与 chat/RAG/wc_* 边界、EP11/EP13；与 [EP07-workflow.md](../../docs/tasks/epics/EP07-workflow.md) 互链
  - 预计文件：1 · 层：`docs/tech/workflow-engine.md`

- [ ] 6.2 `pnpm test:api:harness` 全绿；核对 [EP07-workflow.md](../../docs/tasks/epics/EP07-workflow.md) + [L05 Part B](../../docs/tasks/learning/L05-memory-workflow.md)
  - 预计文件：learning 勾选（epic 叙事已在 propose 阶段写入）
