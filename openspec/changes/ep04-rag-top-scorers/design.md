## Context

- EP04-01 已有 Silver `wc_goals`（3637 行）与 `player_career` 卡（含每人每届进球），但 **无整届 top-N 聚合卡**。
- 向量检索对「射手榜前10名」语义与 **match 卡**（含 "Goals:" 行）更接近，导致召回错位；`player_career` 分散且 embedding 不命中。
- `compute_rag_sufficient`（EP05）只看 `max(score) >= min_score` + 年份匹配，无法识别「榜单问题 vs 比赛片段」。
- 用户环境曾出现 `wc_goals` 为空 — 属 **未跑 events ETL**，非本 change 修复范围；文档与 export 脚本应 fail-fast 或明确提示。

## Goals / Non-Goals

**Goals:**

- 每届世界杯一条 `tournament_scorers:{WC-YYYY}` 事实卡，文本含 **排名、球员、球队、进球数**（默认 top 10，可配置）
- Export / ingest / search 全链路可检索；query「2022世界杯射手榜前10名」top-3 命中该卡
- `rag_sufficient=false` 当 query 为榜单类且 chunks 无聚合射手榜内容
- Harness 锁定回归

**Non-Goals:**

- 改造 pgvector 索引或 Hybrid 检索
- 聊天 SSE / 真流式改造
- 覆盖所有统计类问题（助攻榜、红黄牌榜等 — 可后续同模式扩展）

## Decisions

### D1: 聚合卡 vs 扩展现有 `tournament` 卡

**选择**：新 `entity_type=tournament_scorers`，id `tournament_scorers:WC-2022`。

**理由**：tournament 卡仅 host/winner/dates；射手榜文本较长，独立 chunk 便于向量命中且不影响现有 tournament 召回。

**备选**：写入 `player_career` 批量 — 仍无法一次回答 top 10；弃用。

### D2: 数据来源 SQL

从 `wc_goals` JOIN `wc_players` / `wc_matches` / `wc_tournaments`，按 `tournament_id` 聚合：

- 排除 `own_goal=true`
- `GROUP BY tournament_id, player_id` → 按进球降序取 top N
- 文本格式示例：

```text
[Top Scorers] 2022 FIFA Men's World Cup (WC-2022)
Ranking (goals in tournament, excluding own goals):
1. Kylian Mbappé (FRA) — 8 goals (Golden Boot)
2. Lionel Messi (ARG) — 7 goals
...
```

**理由**：与 EP04-01 设计一致（`top-scorers-summary.csv` 不 ingest，用 goals 聚合）。

### D3: top N 默认值

**选择**：N=10，export 参数 `--top-scorers-limit 10`（CLI 可选）。

### D4: Ingest collection 命名

**选择**：stem `tournament_scorers` → collection `worldcup-tournament_scorers`（与现有 `worldcup-matches` 一致）。

加入 `DEFAULT_COLLECTION_STEMS`；全量 re-ingest 时与其他 5 个 jsonl 一并处理。

### D5: `rag_sufficient` 榜单规则

**选择**：轻量 regex 检测榜单意图（`射手榜|进球榜|金靴|top\s*\d+|前\s*\d+\s*名|排名` 等）。

当意图命中 **且** chunks 中无一满足：

- `external_id` 前缀 `tournament_scorers:`，或
- chunk 文本含 `[Top Scorers]` / `Ranking (` 

→ 返回 `False`（即使 match 卡分数高且含 2022）。

**理由**：EP05 约定 `rag_sufficient` 仅 prompt 提示、不硬路由；但误判 sufficient 会阻止模型调 Tavily **且** 误导「优先用检索上下文」。聚合卡落地后，sufficient 应在命中聚合卡时为 True。

**备选**：retrieve 阶段 query 改写 — scope 大，本 change 不做。

### D6: Spotlight samples

将 `tournament_scorers:WC-2022` 加入 `SPOTLIGHT_CARD_IDS`（替换一条低价值 match 或扩至 11 条 — **保持 10 条**：替换 `match:M-1970-12`）。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| 本地 `wc_goals` 空 → export 无 2022 卡 | export 日志打印各届行数；README 写明先 `run.py events` |
| 仅 top 10 无法答「第 11 名」 | 文档说明 N 可配；V2 可增参数 |
| re-ingest 耗时 / embedding 费用 | 增量 stem 可 `--collections tournament_scorers` 单独 ingest |
| regex 误杀非榜单 query | 单元测试覆盖「2022 决赛比分」仍 sufficient |

## Migration Plan

1. 确认 Silver：`bash scripts/api.sh exec python ../../scripts/etl/worldcup/run.py events`（若 `wc_goals` 为空）
2. Export Gold：`fact_cards.py`（全量或 `--tournament WC-2022`）
3. Ingest：`scripts/etl/rag/ingest_worldcup.py --collections tournament_scorers`（或全量）
4. 验证：`POST /knowledge/search` + harness query
5. 回滚：删除 `worldcup-tournament_scorers` collection 文档即可；无 schema migration

## Open Questions

- 是否在 EP04 史诗新增 Story「4.x 聚合统计卡」而非仅 EP04-01 脚注？→ tasks 含 epic 勾选，人审可定。
- Golden Boot 标注：从 `wc_awards` / standings-refs 表 JOIN，还是 SQL 推断（同分规则）？→ V1 仅标注已知金靴（Mbappé 2022）；其余排名不含奖项名。
