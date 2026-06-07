## Context

- 依赖：`ep04-01-wc-dim-teams`（维度表已入库）
- Bronze：`players.csv`（10,401 行）
- `list_tournaments` 为逗号分隔 **年份**（非 `tournament_id`）

## Goals / Non-Goals

**Goals**

- `wc_players`：姓名、birth_date、female、positions[]、primary_position、wiki
- `wc_player_tournament_years`：`(player_id, year)` 复合唯一
- 校验：`count_tournaments` == 展开行数（源数据已 0 mismatch）
- 多位置球员（388 人）保留完整 `positions[]`

**Non-Goals**

- 按 `year` JOIN `wc_tournaments.id`（V1 仅存 year；后续视图可补）
- matches / squads

## Schema

**wc_players**

| 列 | 来源 |
|:---|:-----|
| `id` | `player_id` |
| `family_name`, `given_name`, `display_name` | 姓名 |
| `birth_date` | ISO date |
| `female` | 0/1 |
| `positions` | `text[]` from GK/DF/MF/FW 列 |
| `primary_position` | 按 GK→DF→MF→FW 首个为 1 的编码 |
| `count_tournaments` | 源列（校验用） |
| `wikipedia_link` | cleaned |

**wc_player_tournament_years**

| 列 | 说明 |
|:---|:-----|
| `player_id` | FK → `wc_players` |
| `year` | int，如 2022 |
| PK | `(player_id, year)` |

## ETL

- 球员 upsert on `id`
- 桥表：先 `DELETE` 全表再 bulk insert（全量 Bronze 重载，~12k 行）

```bash
bash scripts/api.sh exec python ../../scripts/etl/worldcup/run.py players
```
