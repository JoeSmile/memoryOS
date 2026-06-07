## CLI

```bash
bash scripts/api.sh exec python ../../scripts/etl/worldcup/validate.py
bash scripts/api.sh exec python ../../scripts/etl/worldcup/validate.py --tournament WC-2022
```

- 任一检查失败 → **exit 1**
- 输出：检查名、通过/失败、违规计数

## 检查项

| 类别 | 检查 |
|:---|:---|
| 行数 | 全库表行数 vs Bronze 预期 |
| FK | goals/squads/bookings/matches → 父表 0 orphan |
| 业务 | team_match_stats 每场 2 行；player_years = count_tournaments |
| 业务 | 乌龙球 team_id ≠ player_team_id；replay 必有 replay_of |
| 黄金集 | WC-2022：64 场、172 球、决赛 M-2022-64 3-3 |

## 文档

`docs/tech/worldcup-data-model.md` — mermaid ER + 各 `wc_*` 字段摘要，指向 Alembic 003–006。
