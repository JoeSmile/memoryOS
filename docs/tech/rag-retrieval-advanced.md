# RAG 检索进阶 — Sandbox 实验指南

> **用途**：EP04-03 学习与面试准备。V1 `ep04-rag` 主产品只有 **单向量余弦 + 可选 collection 过滤**；本文档介绍 **`scripts/rag/`** 离线 sandbox，用来练 Hybrid、RRF、Rerank、评测基线。  
> **关联**：[EP04-03 史诗](../tasks/epics/EP04-03-rag-retrieval-advanced.md) · [L03 §7.5](../tasks/learning/L03-rag-dual-stack.md) · [切块/Embedding 笔记](./rag-embedding-chunking.md) · [scripts/rag/README.md](../../scripts/rag/README.md)

---

## 1. 为什么要有 Sandbox

| 问题 | 说明 |
|:-----|:-----|
| V1 够不够用？ | 世界杯 Gold 事实卡 ~2.2 万条，**单向量 + collection** 能 Demo、能上线 |
| 学习缺哪块？ | 面试常问 Hybrid、RRF、Cross-encoder Rerank、P@k/MRR，V1 代码里 **故意没做** |
| Sandbox 解决什么？ | **不进** `POST /knowledge/search`；用 Gold jsonl + mock embed 在本地对比多种检索策略 |
| 和 EP04-03 关系 | Story 4.01–4.08 的 **实验台**；正式落地时再 propose 进 `apps/` |

**数据流（离线）**：

```text
data/gold/worldcup/fact_cards/*.jsonl
        ↓ load_fact_cards()
   内存 FactCard 列表
        ↓ vector_rank / keyword_rank / RRF / rerank
   终端打印 top-k（或 P@5 指标）
```

---

## 2. 环境与前缀命令

在 **仓库根目录** 执行；Python 环境走 `apps/api`（与 `pnpm setup:api` 一致）：

```bash
bash scripts/api.sh exec python ../../scripts/rag/<脚本名>.py [参数...]
```

| 依赖 | 说明 |
|:-----|:-----|
| Gold 数据 | `data/gold/worldcup/fact_cards/`（EP04-01 已生成） |
| API Key | **不需要**（复用 `EmbeddingService` 的 mock 向量） |
| DB / ingest | **不需要**（全文在内存里搜） |
| PyYAML | 可选；读 `eval_queries.yaml` 时需要 |

---

## 3. 共享模块 `_common.py`

路径：`scripts/rag/_common.py`。各 sandbox 脚本通过 `import _common` 调用。

### 3.1 数据结构

| 类型 | 字段 | 目的 |
|:-----|:-----|:-----|
| `FactCard` | `id`, `collection`, `entity_type`, `text` | 一条 Gold 事实卡在内存中的表示；`collection` = `worldcup-{stem}` |
| `RankedHit` | `doc_id`, `collection`, `score`, `text_preview` | 单路检索的一条结果；`score` 含义随方法变（相似度 / 重叠数 / RRF 分） |

### 3.2 `load_fact_cards(stems, limit_per_file)`

| 项 | 说明 |
|:---|:-----|
| **功能** | 从 `fact_cards/{stem}.jsonl` 读入 JSONL，组装 `FactCard` 列表 |
| **目的** | 离线 corpus，不依赖 PostgreSQL |
| **默认** | `stems=["matches","player_careers","players"]`，每文件最多 200 行 |
| **参数** | `stems`：文件名（无 `.jsonl`）；`limit_per_file=None` 表示读全文件 |

### 3.3 `mock_embedding(text)` / `vector_rank(query, cards, top_k)`

| 项 | 说明 |
|:---|:-----|
| **功能** | 对 query 与每条 `text` 算 mock 1024 维向量，**余弦相似度**（点积，向量已 L2 归一化）排序 |
| **目的** | 模拟 V1 **bi-encoder 向量检索**；与线上一致使用 `_mock_embedding` |
| **局限** | **无真实语义**——同样文本才相似；用来教 **管线**，不能用来评 embedding 模型质量 |
| **对应产品** | `DocumentChunkRepository.search_similar()` + `EmbeddingService` |

### 3.4 `tokenize(text)` / `keyword_rank(query, cards, top_k)`

| 项 | 说明 |
|:---|:-----|
| **功能** | 简单分词（英文/数字/中文连续串），按 **query 与文档 token 交集个数** 排序 |
| **目的** | **BM25 的极简替身**，演示「关键词路」长什么样 |
| **局限** | 不是 BM25（无 IDF、无长度归一）；生产应换 Postgres `tsvector` 或 `rank_bm25` |
| **擅长 query** | 含 **比分、年份、队名** 等精确 token 的问题 |

### 3.5 `reciprocal_rank_fusion(ranked_lists, k=60, top_k=10)`

| 项 | 说明 |
|:---|:-----|
| **功能** | 多路 **已排序列表** 融合：\( \text{RRF}(d) = \sum_i \frac{1}{k + \text{rank}_i(d)} \) |
| **目的** | Hybrid / 多 query 的标准融合方式；**不要求** 各路分数同尺度 |
| **参数** | `k` 默认 60（文献常用）；`ranked_lists` 为多个 `list[RankedHit]` |
| **面试点** | 比「向量分 × 0.7 + BM25 × 0.3」稳，因为 rank 比 raw score 鲁棒 |

### 3.6 `precision_at_k(hits, expected_id, k)`

| 项 | 说明 |
|:---|:-----|
| **功能** | 期望 `external_id` 是否出现在 top-k 中：在则 1，否则 0 |
| **目的** | Story 4.01 **检索评测** 的最小指标 |
| **扩展** | 多条 query 取平均 → mean P@k；后续可加 MRR、nDCG |

### 3.7 `load_eval_queries()` / `print_hits()`

| 函数 | 功能 |
|:-----|:-----|
| `load_eval_queries` | 读 `scripts/rag/eval_queries.yaml`（需 PyYAML）；失败则用内置 3 条样例 |
| `print_hits` | 格式化打印 top 结果，便于肉眼对比 |

---

## 4. 各 Sandbox 脚本

### 4.1 `sandbox_hybrid.py` — Hybrid 三路对比（Story 4.03）

| 项 | 说明 |
|:---|:-----|
| **功能** | 对同一 query 并行输出：**仅向量**、**仅关键词**、**RRF(向量+关键词)** 三个 top-k |
| **目的** | 理解 Hybrid 何时优于单向量；面试讲「精确 token vs 语义」 |
| **用法** | |

```bash
bash scripts/api.sh exec python ../../scripts/rag/sandbox_hybrid.py \
  --query "1930 France Mexico 4-1" \
  --top-k 5 \
  --stems matches,player_careers \
  --limit 300
```

| 参数 | 默认 | 含义 |
|:-----|:-----|:-----|
| `--query` | （必填） | 用户问句 |
| `--top-k` | 5 | 每路展示条数 |
| `--stems` | `matches,player_careers` | 加载哪些 Gold 文件 |
| `--limit` | 300 | 每个 jsonl 最多读多少行 |

**典型现象**：mock 向量路常排错；关键词路命中 `match:M-1930-01`；Hybrid RRF 把关键词路顶上来。

---

### 4.2 `sandbox_rrf.py` — 多 Query + RRF（Story 4.05）

| 项 | 说明 |
|:---|:-----|
| **功能** | 将 query **改写为多个变体**（stub：如 Messi → Lionel Messi），每变体跑一遍 `vector_rank`，再 RRF 合并 |
| **目的** | 练 **query expansion** 与 **多路 rank 融合**；生产可换 LLM 改写或 HyDE |
| **用法** | |

```bash
bash scripts/api.sh exec python ../../scripts/rag/sandbox_rrf.py \
  --query "Messi World Cup 2022" \
  --top-k 5
```

**面试点**：RRF 不依赖各 list 的分数标度；list 越多，重复出现的 doc 排名越靠前。

---

### 4.3 `sandbox_rerank.py` — 两阶段 Rerank（Story 4.04）

| 项 | 说明 |
|:---|:-----|
| **功能** | **Stage 1**：`vector_rank` 宽召回（`--recall-k`，默认 20）→ **Stage 2**：`stub_cross_encoder_rerank` 窄输出（`--top-k`，默认 5） |
| **目的** | 理解 **bi-encoder 召回 + cross-encoder 精排** 流水线 |
| **Stub 行为** | 用 token 重叠假装 CE 分数；文件内 TODO 标明如何换真实模型 |
| **用法** | |

```bash
bash scripts/api.sh exec python ../../scripts/rag/sandbox_rerank.py \
  --query "1930 France Mexico 4-1" \
  --recall-k 20 \
  --top-k 5
```

**面试点**：CE 对 `(query, doc)` 联合编码，准但慢；只对 top_20 做 rerank 控成本。

---

### 4.4 `sandbox_eval_baseline.py` — P@k 评测（Story 4.01）

| 项 | 说明 |
|:---|:-----|
| **功能** | 读 `eval_queries.yaml`，对带 `expected_id` 的 query 算 **P@k** |
| **目的** | 建立可重复的 **before/after** 数字（加 Hybrid、加 Rerank 后对比） |
| **用法** | |

```bash
# mock 向量基线（语义无意义，P@k 常接近 0）
bash scripts/api.sh exec python ../../scripts/rag/sandbox_eval_baseline.py \
  --mode vector --k 5 --limit 500

# Hybrid 基线（精确 match query 上 P@k 可接近 1）
bash scripts/api.sh exec python ../../scripts/rag/sandbox_eval_baseline.py \
  --mode hybrid --k 5 --limit 500
```

| 参数 | 说明 |
|:-----|:-----|
| `--mode vector` | 仅 `vector_rank` |
| `--mode hybrid` | RRF(`vector_rank`, `keyword_rank`) |
| `--k` | P@k 的 k |
| `--limit` | 每个 jsonl 加载行数 |

**教学对比**（同一 eval 集、limit=500）：

| mode | mean P@5 | 解读 |
|:-----|:---------|:-----|
| vector | ~0 | mock embed 不反映语义 |
| hybrid | ~1.0 | 关键词路拉回含比分/日期的 match 行 |

---

### 4.5 `eval_queries.yaml` — 评测集

| 项 | 说明 |
|:---|:-----|
| **功能** | 固定 query + `expected_id`（Gold 行的 `id` 字段）+ 可选 `collection` |
| **目的** | 扩展 Story 4.01；自己跑 search 后把 Messi 等 query 的 `expected_id` 填实 |
| **编辑** | 新增条目后重跑 `sandbox_eval_baseline.py` |

示例：

```yaml
queries:
  - query: "1930 France Mexico 4-1 group stage"
    expected_id: match:M-1930-01
    collection: worldcup-matches
```

---

## 5. 方法与 V1 产品对照

| Sandbox 方法 | V1 产品（`ep04-rag`） | 何时进产品 |
|:-------------|:----------------------|:-----------|
| `vector_rank` | ✅ `search_similar` + live/mock embed | 已做 |
| `keyword_rank` | ❌ | EP04-03 Story 4.03 |
| `reciprocal_rank_fusion` | ❌ | EP04-03 Story 4.03 / 4.05 |
| stub rerank | ❌ | EP04-03 Story 4.04 |
| `precision_at_k` | ❌ | EP04-03 Story 4.01 Harness |
| collection 过滤 | ✅ API 可选参数 | 已做（metadata，非多路） |

---

## 6. 推荐学习顺序

1. 跑 `sandbox_hybrid.py`，肉眼对比三路结果  
2. 跑 `sandbox_eval_baseline.py` **vector → hybrid**，记住 P@5 差异  
3. 读 `sandbox_rrf.py` 输出，口述 RRF 公式  
4. 跑 `sandbox_rerank.py`，画两阶段示意图（可放面试笔记）  
5. 在 `eval_queries.yaml` 补 10～20 条，写一段对比进 L03 勾选  

---

## 7. 扩展路线（自己练）

| 步骤 | 改动 | 产出 |
|:-----|:-----|:-----|
| 1 | `keyword_rank` → Postgres FTS 或 `rank_bm25` | Hybrid 更接近生产 |
| 2 | `vector_rank` → DB `search_similar` + **live** embed | 语义评测才有意义 |
| 3 | stub rerank → CrossEncoder / Cohere rerank | MRR 对比表 |
| 4 | 结果写入本文 §8 实施记录 | EP04-03 archive 材料 |

---

## 8. 实施记录（Sandbox）

| 日期 | 项 | 记录 |
|:-----|:---|:-----|
| 2026-06-07 | 脚本骨架 | `scripts/rag/*` 可运行；eval 3 条 match query |
| | vector P@5 | mock 下 ~0（预期） |
| | hybrid P@5 | token stub 下 ~1.0（教学用） |
| | 待填 | live embed + 全库 ingest 后的真实 P@5 |

---

## 9. 变更记录

| 日期 | 说明 |
|:-----|:-----|
| 2026-06-07 | 初稿：sandbox 模块与各脚本说明（EP04-03 学习文档） |
