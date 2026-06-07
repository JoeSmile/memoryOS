## Context

- 规划文档：[`docs/superpowers/specs/2026-06-03-worldcup-bronze-etl-plan.md`](../../../docs/superpowers/specs/2026-06-03-worldcup-bronze-etl-plan.md)
- Bronze 路径：`data/bronze/worldcup/`（31 CSV，本地 gitignore；报告进 Git）
- 运行环境：与 `apps/api` 共用 Conda/venv（`bash scripts/api.sh exec python ...`）

## Goals / Non-Goals

**Goals**

- 一键生成 `manifest.json` + `report.md`
- 每文件：sha256、行数、列清单、空值率、候选主键唯一性
- 跨文件：列名共现矩阵、语义别名簇（team_id / home_team_id 等）
- 已知外键对抽检（goals→matches、squads→players 等），结果写入报告

**Non-Goals**

- Alembic / Silver 表
- 修改 CSV 源文件
- pandas 以外的重型依赖（polars、Spark）

## Decisions

### 1. 脚本位置与调用

```bash
# 仓库根目录
python scripts/etl/worldcup/profile.py data/bronze/worldcup/
# 或
bash scripts/api.sh exec python ../../scripts/etl/worldcup/profile.py data/bronze/worldcup/
```

默认输出 `<bronze_dir>/_profile/`。

### 2. manifest 结构

```json
{
  "generated_at": "ISO-8601",
  "bronze_dir": "absolute path",
  "file_count": 31,
  "files": [{ "name", "sha256", "row_count", "columns", "column_stats" }],
  "column_index": { "col_name": ["a.csv", "b.csv"] },
  "semantic_groups": [{ "id", "columns", "notes" }],
  "fk_checks": [{ "child_file", "child_col", "parent_file", "parent_col", "orphan_count" }]
}
```

### 3. 语义别名（配置化）

在 `profile.py` 内 `SEMANTIC_GROUPS` 常量（本 change 不单独 YAML），与规划文档 §列名对齐：

- `team_id` 簇：`team_id`, `home_team_id`, `away_team_id`, `opponent_id`, `player_team_id`
- `score` 簇：`goals_for`, `home_team_score`, …
- 胜负簇：`win` / `home_team_win`, `lose` / `away_team_win`

### 4. 依赖

`pandas` 仅写入 `requirements-dev.txt`，避免 API 运行时硬依赖。

### 5. 测试

`tests/unit/test_worldcup_profile.py` 使用 `scripts/etl/worldcup/fixtures/` 下 2 个迷你 CSV，不依赖全量 Bronze。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| CI 无全量 CSV | 单测用 fixture；全量报告本地生成后提交 `_profile/` |
| 大文件内存 | 约 8 万行，pandas 足够；`player_appearances` 最大 ~27k |

## Migration Plan

无 DB 迁移。合并后运行一次 profile 更新 `_profile/manifest.json` 与 `report.md`。
