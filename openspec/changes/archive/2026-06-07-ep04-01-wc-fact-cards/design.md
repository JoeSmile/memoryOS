## CLI

```bash
bash scripts/api.sh exec python ../../scripts/etl/worldcup/fact_cards.py
bash scripts/api.sh exec python ../../scripts/etl/worldcup/fact_cards.py --tournament WC-2022
```

- 默认输出目录：`data/gold/worldcup/fact_cards/`
- 不写 pgvector；EP04 document loader 直接读 JSONL

## JSONL 记录格式

```json
{
  "id": "match:M-2022-64",
  "entity_type": "match",
  "source_ids": ["M-2022-64", "WC-2022"],
  "text": "[Match] 2022 FIFA World Cup · Argentina vs France · Final · 2022-12-18\n..."
}
```

## 文本模板

| 类型 | 首行 | 正文要点 |
|:---|:---|:---|
| match | `[Match] {year} · {home} vs {away} · {stage} · {date}` | 比分、加时/点球、球场、进球列表 |
| player | `[Player] {name} ({code})` | 出生日、届次年份、位置、大名单次数 |
| tournament | `[Tournament] {name} ({id})` | 日期、东道主、冠军、队数、赛制标志 |

## SQL

- `wc_matches` JOIN teams / stadiums / tournaments
- 进球按 `match_id` 批量拉取 JOIN players
- 球员卡 JOIN `wc_player_tournament_years`；大名单统计来自 `wc_squads`

## samples.jsonl

固定 10 条（2022 决赛、Messi、赛事总览等）供人工 spot-check。
