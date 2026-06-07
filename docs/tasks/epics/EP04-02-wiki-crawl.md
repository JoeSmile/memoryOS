# EP04-02 — Wikipedia 爬虫补充 RAG（**上线后**）

| 属性         | 值                                                                                                      |
| :----------- | :------------------------------------------------------------------------------------------------------ |
| **状态**     | 📋 **已立项 · 暂缓** — **产品上线（EP08）之后再做**                                                     |
| **优先级**   | P2（增强型；不阻塞 EP04 RAG 首版与上线）                                                                |
| **父史诗**   | [EP04 — RAG](./EP04-rag.md)                                                                             |
| **依赖**     | [EP04-01](./EP04-01-worldcup-data-etl.md) ✅ · **`ep04-rag`**（`documents` / `document_chunks`）· **EP08 上线** |
| **OpenSpec** | 未 propose — 上线前排期时再 `/opsx:propose ep04-wiki-crawl`                                             |

> **动机**：CSV/Silver 中已有球队、球员等 **Wikipedia 链接**（元数据），当前仅结构化 **Gold 事实卡** 入 RAG。爬虫可在上线后把百科叙述、背景补进同一 pgvector 库，与事实卡 **互补**（非替代）。

---

## 上线门禁（MUST）

- [ ] **EP08 部署**完成，生产/预发环境稳定可访问
- [ ] **`ep04-rag`** archive：ingest + search 已验证
- [ ] 产品方确认：允许外链抓取策略（限速、来源标注、失败降级）

**在此之前禁止** 开 `apps/` 爬虫业务代码（可只维护本文档）。

---

## 目标（V1 草案）

从 Silver `wc_teams` / `wc_players`（等）读取 **wiki URL** → 抓取/拉取正文 → 清洗 → **切块** → 写入既有 `documents` / `document_chunks`（`collection` 如 `worldcup-wiki-teams`、`worldcup-wiki-players`）。

| 能力           | 说明                                                         |
| :------------- | :----------------------------------------------------------- |
| 数据源         | CSV 中已有 `*_wikipedia_link`，非重新扫 31 个 CSV            |
| 抓取方式       | 优先 **MediaWiki API**，避免裸爬 HTML；限速 + 缓存           |
| 实体对齐       | `metadata` 绑定 `team_id` / `player_id` + 源 URL             |
| 与事实卡关系   | 事实卡 = 结构化可核对；Wiki = 叙述补充；检索可 `collection` 过滤 |
| 异步           | 后台任务/队列，不阻塞 API（对齐 EP04 Story 4.2 思路）        |

---

## 非目标（V1）

- 替代 EP04-01 结构化 ETL 或 Gold 事实卡
- 通用任意 URL 爬虫（仅世界杯实体 wiki）
- 上线前在 CI/Harness 依赖外网实时爬取

---

## 风险与合规（立项备忘）

| 项     | 注意                                                         |
| :----- | :----------------------------------------------------------- |
| ToS    | 遵守站点 robots / API 条款；响应头注明数据来源               |
| 质量   | 页眉脚、信息框需清洗；见 [`rag-embedding-chunking.md`](../../tech/rag-embedding-chunking.md) 路径 B |
| 去重   | 与 Gold 事实卡 `external_id` 区分（如 `wiki:player:P-xxx`）  |
| 成本   | 页数 × embedding；宜增量 re-crawl                              |

---

## 建议 OpenSpec 拆分（上线后再 propose）

1. **Bronze**：URL 队列 + 原始 HTML/JSON 缓存（`data/bronze/worldcup/wiki/`）
2. **Ingest**：解析 → chunk → embed → 同库 `collection` 前缀 `worldcup-wiki-*`
3. **Ops**：CLI `crawl_worldcup_wiki.py`、可选管理端触发 re-crawl

---

## 同步学习

- [ ] MediaWiki API 与礼貌爬取
- [ ] HTML 清洗（trafilatura / readability 类方案调研）
- [ ] 与结构化事实卡在 RAG 中的重排/去重

---

## 变更记录

| 日期       | 说明                                       |
| :--------- | :----------------------------------------- |
| 2026-06-03 | 立项：用户确认上线后再做；本文档为唯一留底 |
