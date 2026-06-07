## Scope (P1)

| 表 | 来源 | 行数 |
|:---|:-----|-----:|
| `wc_goals` | goals.csv | 3,637 |
| `wc_squads` | squads.csv | 13,843 |
| `wc_bookings` | bookings.csv | 3,178 |

## 清洗

- 宽表冗余列（`*_name`）不入库
- `shirt_number=0` → NULL
- `own_goal`/`penalty`/牌标志 → boolean
- `wc_squads` PK：`(tournament_id, team_id, player_id)`

## 依赖

须先跑 `dimensions` → `players` → `matches`。
