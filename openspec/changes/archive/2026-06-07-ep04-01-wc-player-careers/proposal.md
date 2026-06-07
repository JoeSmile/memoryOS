## Why

基础 `players.jsonl` 缺进球/出场/奖项聚合，RAG 难以回答「Messi 世界杯进了几球」类问题。

## What Changes

- 新增 `player_careers.jsonl`（`entity_type: player_career`）
- 从 Silver 聚合：进球（按届）、出场（首发/替补）、奖项、代表队
- 更新 `samples.jsonl` 球员条目为 enriched 卡
