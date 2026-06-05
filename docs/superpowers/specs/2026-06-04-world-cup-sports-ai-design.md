# 世界杯足球 · AI 量化分析（学习项目）设计 spec

> **状态**：brainstorming 定稿（2026-06-04）  
> **范围**：仅足球；Phase A = 赛会实力分 + 球队榜；Phase B = 单场赛前强度对比  
> **非目标**：博彩、赔率、投注建议  
> **MemoryOS**：独立史诗 **EP11**（`ep11-wc-sports`
> 待定），不替代 EP02–EP10 主线

---

## 1. 范围与分期

### 1.1 产品定位

- 展示国家队、球员、**可复现战力分**（0–100）、排名与 AI 文字解读。
- 页脚固定：**学习项目 / 非官方数据 / 不构成任何投注或博彩建议**。

### 1.2 Phase A（V1 MVP）

| 交付      | 说明                                              |
| :-------- | :------------------------------------------------ |
| 数据      | Seed 驱动；首届数据 `tournament_id=wc2022`        |
| 战力分 A  | Python 确定性公式 + `breakdown` JSON              |
| LangGraph | stats → compute → LLM 报告（不得改分）            |
| API       | **按 `tournament_id` 参数化**（见 §4）            |
| 前端      | `/sports/[tournamentId]/…` 球队榜、详情、SSE 简评 |

### 1.3 Phase B（V2）

- 赛前两队 **优势指数**（非赔率）。
- API：`POST .../matchup?home=&away=` 或等价路径。
- 复用同一 `tournament_id` 与 stats 层。

### 1.4 YAGNI

- NBA、联赛长周期、出线概率 Monte Carlo（V3）、RAG 新闻（EP04 后可选增强）。

---

## 2. 数据模型

### 2.1 赛会（多届扩展）

```text
tournaments
  id          TEXT PK   -- "wc2022" | "wc2026"
  name        TEXT      -- "FIFA World Cup 2022"
  year        INT
  status      TEXT      -- seeding | active | completed
```

所有业务表带 **`tournament_id` FK**，避免按届复制 schema。

### 2.2 实体表

| 表                      | 关键字段                                                                      |
| :---------------------- | :---------------------------------------------------------------------------- |
| `teams`                 | `tournament_id`, `code` (FRA), `name`, `group_name`, `eliminated_stage`       |
| `players`               | `tournament_id`, `team_id`, `name`, `position`, `shirt_number`                |
| `matches`               | `tournament_id`, `stage`, `home_team_id`, `away_team_id`, scores, `played_at` |
| `team_match_stats`      | 每场技术统计（可空）                                                          |
| `team_tournament_stats` | 赛会累计 + **物化** `power_index`, `rank`, `breakdown`                        |

**V1 数据**：`apps/api/data/seed/{tournament_id}/`（如 `wc2022/`）JSON/CSV +
seed 命令。  
**V1.1+**：`IngestService` 从外部 API 写入同一 schema（`wc2026`
新目录或新 ingest job）。

### 2.3 战力分 A

- 计算：`PowerIndexService.compute(tournament_id, team_id)` →
  `{ power_index, rank, breakdown }`。
- 子项在当届参赛队集合内归一化；权重来自配置（YAML/env）。
- **单测 + Harness**：对 `wc2022` seed 快照断言分数/排名。

### 2.4 Phase B 预留

- `MatchupService.advantage(tournament_id, home_id, away_id)` 复用
  `power_index` + 主客/淘汰赛系数；V1 不实现。

---

## 3. LangGraph 与 AI

### 3.1 图（`sports_team_analysis_graph`）

```text
START → fetch_team_stats
     → compute_power_index   # 调用 PowerIndexService，写回 state
     → generate_report       # LLM + breakdown，SSE 可选
     → END
```

- **Tools / DB**：节点只读 `team_tournament_stats`；禁止 LLM 修改数值。
- **可观测**：LangSmith；可选对比 run（无数据 vs 有数据）。

### 3.2 与 MemoryOS 栈映射

| 技术      | 用途                              |
| :-------- | :-------------------------------- |
| LangGraph | 多节点编排                        |
| LangSmith | Trace、延迟、Prompt 调试          |
| SSE       | 流式简评（复用 EP02 client 模式） |
| Harness   | 契约 + mock 流                    |
| EP04+ RAG | 可选：规则 FAQ、新闻（非 V1）     |

---

## 4. API 设计（`tournament_id` 参数化）

**原则**：路径中 **不写死 `wc2022`**，统一 `tournaments/{tournament_id}`，便于
`wc2026` 仅增 seed/ingest。

| 方法 | 路径                                                                 | 说明                                          |
| :--- | :------------------------------------------------------------------- | :-------------------------------------------- |
| GET  | `/api/v1/sports/tournaments`                                         | 列表：`wc2022`, `wc2026`（metadata）          |
| GET  | `/api/v1/sports/tournaments/{tournament_id}/teams`                   | 战力榜：`power_index`, `rank`, `code`, `name` |
| GET  | `/api/v1/sports/tournaments/{tournament_id}/teams/{team_id}`         | 详情 + `breakdown`                            |
| GET  | `/api/v1/sports/tournaments/{tournament_id}/teams/{team_id}/players` | 球员列表                                      |
| POST | `/api/v1/sports/tournaments/{tournament_id}/teams/{team_id}/analyze` | SSE：AI 简评                                  |

**校验**：

- 未知 `tournament_id` → `40401`（统一 envelope）。
- `team_id` 不属于该届 → `40401`。

**Phase B（V2）示例**：

| 方法 | 路径                                                                                        |
| :--- | :------------------------------------------------------------------------------------------ |
| POST | `/api/v1/sports/tournaments/{tournament_id}/matchup` body: `{ home_team_id, away_team_id }` |

**鉴权**：榜单/详情可公开只读；`analyze` / `matchup` 建议 JWT（与聊天共用）。

---

## 5. 前端

| 路由                                    | 说明                                         |
| :-------------------------------------- | :------------------------------------------- |
| `/sports`                               | 赛会选择（卡片：wc2022、wc2026 coming soon） |
| `/sports/[tournamentId]`                | 球队排行榜                                   |
| `/sports/[tournamentId]/teams/[teamId]` | 详情 + breakdown + 球员 + AI 简评            |

- `tournamentId` 与 API `tournament_id` 一致（字符串 slug）。
- 切换届别 = 改 URL 参数，**无硬编码 2022**。

---

## 6. 工程与排期

### 6.1 OpenSpec

- 建议 change 名：`ep11-wc-sports`（或 `ep11-sports-football`）。
- **启动时机**：`ep02-program` Phase 7 完成后再 propose（遵守 AGENTS 栅栏）。

### 6.2 建议 tasks 分期

| Task 块 | 内容                                                                   |
| :------ | :--------------------------------------------------------------------- |
| A1      | `tournaments` schema + `wc2022` seed + `PowerIndexService` + GET teams |
| A2      | LangGraph analyze + SSE + harness                                      |
| A3      | 前端 `/sports/[tournamentId]`                                          |
| B       | `matchup` API + 对比页                                                 |
| 后续    | `wc2026`：新 seed 或 ingest job，**无 API 路径变更**                   |

### 6.3 新增 `wc2026` 检查清单

- [ ] `data/seed/wc2026/` 或 ingest 管道
- [ ] `tournaments` 表插入一行 `id=wc2026`
- [ ] 前端赛会列表展示
- [ ] （可选）重新跑 `PowerIndexService` 全量计算

---

## 7. 风险与合规

| 风险               | 缓解                                       |
| :----------------- | :----------------------------------------- |
| 数据版权 / API ToS | Seed 注明来源；商用 API 单独评估           |
| LLM 编造数据       | 报告只引用 `breakdown` 中数字；Prompt 约束 |
| 被误解为博彩       | UI 免责声明 + 禁止赔率文案                 |
| 赛会外无数据       | `tournaments.status` + 空态页              |

---

## 8. 自检（spec review）

- [x] 无 TBD 占位阻塞 V1
- [x] `tournament_id` 贯穿 DB / API / 前端，支持 `wc2026`
- [x] 分数由代码计算，与 LLM 职责分离
- [x] Phase A / B 边界清晰
- [x] 不阻塞 EP02 Program

---

## 9. 下一步

1. 你 review 本 spec，确认或批注修改。
2. `/opsx:propose ep11-wc-sports`（或等价）生成 tasks.md。
3. `writing-plans` 拆 implementation plan。
4. **不要**在 EP02 未完成前改 `apps/` 实现本史诗。
