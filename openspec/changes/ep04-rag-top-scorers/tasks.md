## 0. Human review（apply 前必过）

> propose 完成后 **必须停在这里**等人审；未勾选前 **禁止**写业务代码。

- [ ] **Tasks reviewed by human** — 人审通过后再 `/opsx:apply`、`/work-next` 或说「继续实现」

### Review checklist

- [ ] 前置：`wc_goals` 已加载（`run.py events`）或 accept export 空卡风险
- [ ] design D5 榜单 `rag_sufficient` 规则与 EP05「仅 prompt 提示」一致（不硬禁 Tavily）
- [ ] Harness 覆盖「2022世界杯射手榜前10名」检索 + 非榜单 query 不回退
- [ ] 与 `EP04-rag` / `EP04-01` 史诗勾选一致；无 Hybrid/重排 scope 膨胀
- [ ] 每条 task ≤3 文件 / ~150 行

**Reviewer notes:**

---

## 1. Gold ETL — tournament_scorers 事实卡

- [ ] 1.1 `build_tournament_top_scorers_card_text` + `generate_tournament_scorer_cards`（`wc_goals` 聚合，排除 OG，top N=10）
  - 预计文件：2 · 层：`apps/api/app/etl/worldcup/fact_cards.py` + `tests/unit/test_worldcup_fact_cards.py`
  - 验收：单测含 WC-2022 mock 行 → Mbappé 8 球排第 1

- [ ] 1.2 Export 接线：`tournament_scorers.jsonl` + `SPOTLIGHT` 换入 `tournament_scorers:WC-2022`
  - 预计文件：2 · 层：`fact_cards.py` + `data/gold/worldcup/fact_cards/samples.jsonl`（重跑 export 后更新）
  - 验收：`export_fact_cards` 返回 counts 含 `tournament_scorers`

## 2. Ingest — 新 collection

- [ ] 2.1 `DEFAULT_COLLECTION_STEMS` 增加 `tournament_scorers` + ingest 单测
  - 预计文件：2 · 层：`knowledge_ingest_service.py` + `tests/unit/test_knowledge_ingest_service.py`（或现有 ingest 测）
  - 验收：stem → `worldcup-tournament_scorers`

- [ ] 2.2 文档：Gold README / `EP04-01` 复现命令补充 export + `--collections tournament_scorers` ingest
  - 预计文件：2 · 层：`data/gold/worldcup/fact_cards/README.md` + `docs/tasks/epics/EP04-01-worldcup-data-etl.md`

## 3. RAG — 榜单 query 充分性

- [ ] 3.1 `compute_rag_sufficient` 榜单意图 + 聚合卡检测（design D5）
  - 预计文件：2 · 层：`graphs/prompts/unified_react.py` + `tests/unit/test_unified_react_prompt.py`
  - 验收：仅 match 卡 +「射手榜」→ false；含 `tournament_scorers:WC-2022` → true

## 4. Harness & 验收

- [ ] 4.1 检索回归：ingest samples（含 WC-2022 scorers）后 search top-3 命中 `tournament_scorers:WC-2022`
  - 预计文件：2 · 层：`tests/harness/test_rag_retrieval_contract.py`（或新建 `test_top_scorers_retrieval.py`）
  - 前置：harness 用 mock embed；samples 含新 spotlight 卡

- [ ] 4.2 更新 `docs/tasks/epics/EP04-rag.md` Story 勾选 + change 链接
  - 预计文件：1 · 层：docs

## 5. 本地复现（ops，可选人工）

- [ ] 5.1 本地：`run.py events` → export → ingest → chat 问「2022世界杯射手榜前10名」无 Tavily、sources 含 scorers 卡
  - 预计文件：0 · 层：人工验收 checklist（可写在 task 4.2 或 PR Test plan）
