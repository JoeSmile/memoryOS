# EP04-01 — 世界杯 CSV 数据清洗与 Silver 层（EP04 前置）

| 属性         | 值                                                                                                                                                          |
| :----------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **状态**     | ✅ **已完成**（2026-06-07）— 7 个子 change 已 archive                                                                                                       |
| **周期**     | EP04 第 1 周（约 1–1.5 周）                                                                                                                                 |
| **优先级**   | P0（阻塞 EP04 RAG / Neo4j / EP11 赛会数据）                                                                                                                 |
| **父史诗**   | [EP04 — RAG](./EP04-rag.md)                                                                                                                                 |
| **依赖**     | EP03（PostgreSQL + Alembic）                                                                                                                                |
| **后续**     | EP04（向量 RAG）· EP11 世界杯分析（[`world-cup-sports-ai-design`](../../superpowers/specs/2026-06-04-world-cup-sports-ai-design.md)）· Neo4j（可选 change） |
| **目标文档** | `docs/tech/worldcup-data-model.md` 📋 · `docs/database.md` 增补                                                                                             |
| **规划留底** | [`2026-06-03-worldcup-bronze-etl-plan.md`](../../superpowers/specs/2026-06-03-worldcup-bronze-etl-plan.md)（31 文件盘点 + 方案/难点）                       |
| **数据**     | **31 个 CSV** 已放入 `data/bronze/worldcup/`                                                                                                                |

> **为何单独成史诗**：数据源是
> **结构化 relational + 双行比赛宽表**，不是 PDF 文档；清洗、实体对齐、外键校验、文本化是
> **独立工程**，不应与 EP04 的 embedding/RAG 管线混在一个 PR。

---

## 已见 3 张表（样例）与清洗要点

### 1. `teams`（国家队维度）

| 列（样例）                  | 说明          | 清洗动作                          |
| :-------------------------- | :------------ | :-------------------------------- |
| `team_id` (`T-01`)          | 主键          | 全库统一引用                      |
| `team_code` (`ARG`)         | FIFA/ISO 三字 | 与 `team_name` 建 alias 表        |
| `confederation_*`           | 大洲足联      | 拆为 `confederations` 维度        |
| `federation_*`              | 国家足协      | 拆为 `federations` 维度           |
| `mens_team` / `womens_team` | 0/1           | V1 男子世界杯可先滤 `mens_team=1` |
| `*_wikipedia_link`          | URL           | 存元数据；`not applicable` → NULL |

### 2. `players`（球员维度）

| 列（样例）                   | 说明           | 清洗动作                              |
| :--------------------------- | :------------- | :------------------------------------ |
| `player_id` (`P-35894`)      | 主键           |                                       |
| `family_name` / `given_name` | 姓名           | 合成 `display_name`；注意编码         |
| `birth_date`                 | `YYYY/M/D`     | → ISO date                            |
| `goal_keep`…`forward`        | 四列 0/1       | → `positions[]` 或主位置枚举          |
| `list_tournaments`           | `"1995, 1999"` | **拆为多行** `player_tournament` 关系 |
| `count_tournaments`          | 计数           | 校验与 `list_tournaments` 一致        |
| `female`                     | 0/1            | 男子世界杯样本可筛 `female=0`         |

### 3. `matches`（比赛主表 — **已归一 1 行/场**）

> **盘点修正**：实测 `matches.csv` 已是 `home_team_id` / `away_team_id` 单列；**双行球队视角在 `team_appearances.csv`**（2,496 行 = 1,248 场 × 2）。详见规划文档 §4.1。

`matches` 列含主客比分、`replayed`/`replay`、点球等；`team_appearances` 列含 `team_*` 与 `opponent_*` 镜像。

| 列（样例）                    | 说明       | 清洗动作                                                                  |
| :---------------------------- | :--------- | :------------------------------------------------------------------------ |
| `match_id` (`M-2022-22`)      | 比赛主键   | `matches` 直导 `wc_matches`（无需双行合并）                               |
| `home_team_id` / `away_team_id` | 本场双方 | 直接入库；与 `team_appearances` 交叉校验                                  |
| `home_team_score` / `away_team_score` | 比分 | 直导；勿解析 `score` 字符串（含 Unicode 破折号）                          |
| `stage_name` / `group_name`   | 阶段       | 枚举标准化（group / r16 / qf / sf / final…）                              |
| `stadium_id` / `city_name`    | 场地       | 拆 `stadiums` 维度                                                        |
| `extra_time` / `penalties`    | 加时/点球  | 布尔 + 点球比分（若有列）                                                 |

**核心 ETL 规则（matches + team_appearances）**：

```text
matches.csv (1 行/场) → wc_matches
team_appearances.csv (2 行/场) → wc_team_match_stats
  → 校验：每场恰好 2 行；rowA.team_id = rowB.opponent_id；比分与 wc_matches 一致
```

---

## 三层数据架构（本史诗交付 Silver）

```text
Bronze   data/bronze/worldcup/*.csv     原文件 + file_hash + 行数元数据
   ↓      scripts/etl/worldcup/profile.py
Silver   PostgreSQL 规范化表            本史诗主交付（见下）
   ↓      （EP04-02+）文本事实卡 / Neo4j 导入
Gold     document_chunks / 图节点       交给 EP04 RAG、Neo4j change
```

### Silver 核心表（V1 最小集）

与
[EP11 赛会模型](../../superpowers/specs/2026-06-04-world-cup-sports-ai-design.md)
对齐，并支持 **多届**（`tournament_id` 或 `edition_year`）：

| 表                      | 来源 CSV（预期）                |
| :---------------------- | :------------------------------ |
| `wc_tournaments`        | tournaments / 从 match 推导     |
| `wc_confederations`     | teams                           |
| `wc_teams`              | teams                           |
| `wc_players`            | players                         |
| `wc_player_tournaments` | players.`list_tournaments` 展开 |
| `wc_stadiums`           | matches                         |
| `wc_matches`            | matches（去重后）               |
| `wc_match_teams`        | matches（双行展开，可选）       |

其余 ~27 个 CSV 在 **Story 01.1 资产盘点**
后再映射（常见：goals、cards、squads、referees、penalties…）。

---

## Story 映射（建议 OpenSpec 拆分）

### Story 01.1 资产盘点与 Bronze

- [x] 31 文件清单：文件名、行数、主键、外键、样例异常（见 `_profile/manifest.json`）
- [x] `data/bronze/worldcup/` 目录约定 + `.gitignore` 大文件策略
- [x] `scripts/etl/worldcup/profile.py` 输出 profiling 报告（JSON/MD）

### Story 01.2 维度表 ETL（teams → confederations / teams）

- [x] Dimension loader：清洗 wikipedia、`not applicable`；`run.py dimensions`
- [x] Alembic 003：`wc_confederations`、`wc_teams`、`wc_tournaments`、`wc_stadiums`
- [x] 入库验收：6 / 88 / 30 / 240 行（与 CSV 一致）

### Story 01.3 球员 ETL（players）

- [x] 日期、位置列、姓名规范化（`birth_date` 未知 78 条 → NULL）
- [x] `list_tournaments` 拆表 `wc_player_tournament_years`（13,843 行）
- [x] 校验：`count_tournaments` = 展开行数（加载时 fail-fast）

### Story 01.4 比赛 ETL（matches 直导 + team_appearances）

- [x] `matches` → `wc_matches`；`team_appearances` → `wc_team_match_stats`
- [x] 重赛 `replayed`/`replay` → `replay_of_match_id`（8 场，4 对）
- [x] 校验：每场 2 行 team_appearances、比分一致（加载时 fail-fast）

### Story 01.4b 比赛事件 ETL（P1）

- [x] `goals` → `wc_goals`（含 `team_id` / `player_team_id` 乌龙语义）
- [x] `squads` → `wc_squads`（PK: tournament + team + player）
- [x] `bookings` → `wc_bookings`

### Story 01.5 跨表集成校验

- [x] 引用完整性脚本（失败即非 0 exit）
- [x] 覆盖 2022（或你手头最完整一届）黄金数据集
- [x] `docs/tech/worldcup-data-model.md` ER 图 + 字段说明

### Story 01.6 文本事实卡（衔接 EP04，轻量）

- [x] 从 Silver 生成 match / player / tournament 摘要 Markdown 或 JSONL
- [x] 输出到 `data/gold/worldcup/fact_cards/`（**不写 pgvector**，留给 EP04）
- [x] 样例 10 条人工 spot-check

---

## 与 EP04 / RAG / Neo4j / Graph RAG 的分工

| 能力                    | 本史诗 EP04-01 | 后续 change                                     |
| :---------------------- | :------------- | :---------------------------------------------- |
| CSV 清洗、Silver PG     | ✅             |                                                 |
| pgvector + chunk + 检索 |                | **EP04** `ep04-rag`                             |
| Neo4j 点边导入          |                | `ep04-worldcup-kg` 或 EP11                      |
| Graph RAG 社区摘要      |                | V2（KG 稳定后）                                 |
| 聊天里问世界杯          |                | EP04 接入 fact_cards + 可选 Cypher tool（EP05） |

**推荐栈（2 个先落地）**：**Silver PG + 事实卡 RAG**；Neo4j 作为
**并行 change**，用同一 Silver 导出。

---

## OpenSpec（已 archive）

| Change | Story | Archive |
| :----- | :---- | :------ |
| `ep04-01-wc-profile` | 01.1 盘点 | [`2026-06-07-ep04-01-wc-profile`](../../../openspec/changes/archive/2026-06-07-ep04-01-wc-profile/) |
| `ep04-01-wc-dim-teams` | 01.2 维度 | [`2026-06-07-ep04-01-wc-dim-teams`](../../../openspec/changes/archive/2026-06-07-ep04-01-wc-dim-teams/) |
| `ep04-01-wc-players` | 01.3 球员 | [`2026-06-07-ep04-01-wc-players`](../../../openspec/changes/archive/2026-06-07-ep04-01-wc-players/) |
| `ep04-01-wc-matches` | 01.4 比赛 | [`2026-06-07-ep04-01-wc-matches`](../../../openspec/changes/archive/2026-06-07-ep04-01-wc-matches/) |
| `ep04-01-wc-events` | 01.4b 事件 | [`2026-06-07-ep04-01-wc-events`](../../../openspec/changes/archive/2026-06-07-ep04-01-wc-events/) |
| `ep04-01-wc-validate` | 01.5 校验 | [`2026-06-07-ep04-01-wc-validate`](../../../openspec/changes/archive/2026-06-07-ep04-01-wc-validate/) |
| `ep04-01-wc-fact-cards` | 01.6 事实卡 | [`2026-06-07-ep04-01-wc-fact-cards`](../../../openspec/changes/archive/2026-06-07-ep04-01-wc-fact-cards/) |

**Git commits**：`171446f`（Silver ETL + validate）· `5ceded2`（Gold fact-cards）

---

## 验收（复现命令）

```bash
pnpm db:migrate

# 盘点
python scripts/etl/worldcup/profile.py

# Silver ETL（顺序）
bash scripts/api.sh exec python ../../scripts/etl/worldcup/run.py dimensions
bash scripts/api.sh exec python ../../scripts/etl/worldcup/run.py players
bash scripts/api.sh exec python ../../scripts/etl/worldcup/run.py matches
bash scripts/api.sh exec python ../../scripts/etl/worldcup/run.py events

# 校验
bash scripts/api.sh exec python ../../scripts/etl/worldcup/validate.py
bash scripts/api.sh exec python ../../scripts/etl/worldcup/validate.py --tournament WC-2022

# Gold 事实卡
bash scripts/api.sh exec python ../../scripts/etl/worldcup/fact_cards.py
```

- [x] 2022（或选定届次）**0 校验错误**
- [x] `worldcup-data-model.md` 与 Alembic 一致
- [x] 事实卡样例可人工读通

---

## 风险

| 风险                                       | 缓解                                        |
| :----------------------------------------- | :------------------------------------------ |
| 30 个 CSV schema 不一致                    | 先 profile 再写 loader，勿假设              |
| matches 双行边界 case（弃权、replay）      | `replayed`/`replay` 列单独规则              |
| 球员跨届 `list_tournaments` 与比赛表对不上 | 先维度入库，交叉校验放 Story 01.5           |
| 工作量吞掉 EP04 进度                       | **强制** 本史诗单独排期，EP04 只做 RAG 管线 |

---

## 交付摘要

| 层 | 路径 / 表 | 规模 |
| :--- | :--- | ---: |
| Bronze | `data/bronze/worldcup/*.csv`（gitignore）+ `_profile/` | 31 CSV |
| Silver | Alembic `003`–`006`，11 张 `wc_*` 表 | 见 [`worldcup-data-model.md`](../../tech/worldcup-data-model.md) |
| Gold | `data/gold/worldcup/fact_cards/*.jsonl` | 1248 / 10401 / 30 + 10 samples |
| 工具 | `scripts/etl/worldcup/{profile,run,validate,fact_cards}.py` | |

**WC-2022 黄金集**：64 场 · 172 球 · 831 名单 · 决赛 3–3（validate 24+4 项全绿）。

**未做（P2，另开 change）**：substitutions、penalty_kicks、player_appearances、referees 等 ~20 张剩余 CSV。

---

## 下一步（EP04）

1. **EP04 RAG** — document loader 读 `fact_cards/*.jsonl` → chunk → pgvector（见 [EP04-rag](./EP04-rag.md)）
2. 可选并行：`ep04-worldcup-kg`（Neo4j）或 EP11 赛会 API

---

## 同步学习

- [ ] [L03 §1 文档摄入](../learning/L03-rag-dual-stack.md) — 结构化 vs 非结构化
- [ ] pandas/polars profiling
- [ ] 星型/雪花 schema 基础
- [ ] 可选：Neo4j 数据建模预习（不必本史诗实现）
