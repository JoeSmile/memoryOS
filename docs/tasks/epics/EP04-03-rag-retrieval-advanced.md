# EP04-03 — RAG 检索进阶（Hybrid / 重排 / 多路召回）

| 属性 | 值 |
|:-----|:---|
| **状态** | 📋 **已立项 · 暂缓** — **`ep04-rag` V1 闭环后再做**（可与 EP08 后并行排期） |
| **优先级** | P2（**学习 + 召回增强**；不阻塞世界杯事实卡首版） |
| **父史诗** | [EP04 — RAG](./EP04-rag.md) |
| **依赖** | **`ep04-rag` archive**（ingest + `POST /knowledge/search` 单向量已验证）· [EP04-01](./EP04-01-worldcup-data-etl.md) ✅ |
| **学习路线** | [L03 §7.5 检索进阶](../learning/L03-rag-dual-stack.md#75-检索进阶ep04-03--sandbox-实验) · [L07](../learning/L07-optimization.md) |
| **OpenSpec** | 未 propose — 开干前 `/opsx:propose ep04-rag-retrieval-advanced`（可按 Story 拆多个 change） |
| **目标文档** | [`rag-retrieval-advanced.md`](../../tech/rag-retrieval-advanced.md) ✅ · sandbox 见 [`scripts/rag/README.md`](../../../scripts/rag/README.md) |

> **动机**：当前 `ep04-rag` V1 只有 **单路 pgvector 余弦检索**（+ 可选 `collection` 过滤）。对 ~2.2 万条 Gold 事实卡足够上线，但 **面试与进阶 RAG** 还缺 Hybrid、重排、多路融合、评测等一整块。本 epic 专门补这块：**产品可暂缓，学习不可缺**。

---

## 与 V1 的边界

| 能力 | `ep04-rag` V1 | 本 epic |
|:-----|:--------------|:--------|
| 向量检索 | ✅ `embedding <=> query` + `top_k` | 保留为 **一路** |
| collection / metadata 过滤 | ✅ SQL `WHERE` | 扩展为 **预过滤 + 多路** |
| BM25 / 全文 | ❌ | ✅ Story 4.03 |
| Hybrid 融合 | ❌ | ✅ Story 4.03 |
| Cross-encoder 重排 | ❌ | ✅ Story 4.04 |
| 多 Query / RRF | ❌ | ✅ Story 4.05 |
| Query 改写 / HyDE | ❌ | ✅ Story 4.05（可选） |
| MMR 多样性 | ❌ | ✅ Story 4.06 |
| 分数阈值拒答 | 📋 EP04 Story 4.6 提及 | ✅ 与检索层联调 |
| HNSW / IVFFlat | V1 暴力 scan | ✅ Story 4.07 |
| 检索质量 Harness | L2 rubric 预留 | ✅ Story 4.08 |

**V1 不做的原因（备忘）**：事实卡短文本、实体清晰；单向量 + 过滤已能 Demo；先闭环 ingest/search，避免 scope 膨胀。

---

## 启动门禁（MUST）

- [ ] **`ep04-rag`** archive：`KnowledgeSearchService` + Harness 绿
- [ ] 固定 **20～50 条** 世界杯问答作检索评测集（query + 期望 `external_id` / collection）
- [ ] 团队确认：允许引入额外依赖（如 `rank_bm25`、cross-encoder 模型或 API）

**在此之前禁止** 在 `apps/` 主链路默认开启多路检索（可用 **`scripts/` sandbox** 做实验，见下）。

---

## 技术路线图（建议顺序）

```text
Phase 0  评测基线（单向量 top_k 的 P@5 / MRR）
    ↓
Phase 1  分数阈值 + HNSW（单路增强，改动小）
    ↓
Phase 2  BM25 + Hybrid（Postgres tsvector 或 sidecar）
    ↓
Phase 3  Reranker（对 top_20 → top_5）
    ↓
Phase 4  多 Query + RRF（可选 HyDE）
    ↓
Phase 5  接入 LangGraph retrieve 节点 / 配置开关
```

---

## Story 4.01 — 检索评测基线（先做）

**目标**：没有指标，调优是玄学。

- [ ] `harness/cases/rag_retrieval.yaml`：固定 query 集 + 期望命中 id
- [ ] 脚本：单向量 baseline → 输出 P@k、MRR、Recall@k
- [ ] 文档：baseline 数字写入 `rag-retrieval-advanced.md` §1

**面试点**：如何定义「检检索对了」？离线集 vs 在线点击。

---

## Story 4.02 — 分数阈值与拒答

**目标**：低相似度不硬答（对齐 EP04 Story 4.6）。

- [ ] `KnowledgeSearchService`：`min_score` 或 max distance 参数
- [ ] 响应：`chunks=[]` + `reason=no_relevant_results`（契约进 Harness）
- [ ] 在评测集上扫阈值曲线（precision ↑ recall ↓）

**面试点**：阈值怎么定？业务 vs 统计 vs A/B。

---

## Story 4.03 — 关键词 + Hybrid 检索

**目标**：补 **专有名词、比分、球衣号** 等向量弱项。

| 方案 | 做法 | 适用 |
|:-----|:-----|:-----|
| **A. Postgres FTS** | `tsvector` on `content` + `plainto_tsquery` | 与 pgvector 同库，运维简单 |
| **B. BM25 库** | 内存 `rank_bm25` / Elasticsearch | 中文分词需额外配置 |

- [ ] 选定 **A 或 B** 并写入 §6 决策表
- [ ] 第二路召回：`keyword_top_k` + `vector_top_k`
- [ ] **RRF 融合**（见 Story 4.05）或 weighted sum
- [ ] Harness：至少 3 条「数字/全名」query baseline 提升

**面试点**：Hybrid 为什么有效？向量与 BM25 各擅长什么？

---

## Story 4.04 — Cross-encoder 重排

**目标**：粗召回 top_20 → 精排 top_5。

- [ ] 接入方式二选一：**本地 small CE 模型** / **Cohere rerank API** / 百炼若提供 rerank
- [ ] `RerankService`：输入 `(query, chunk_text[])` → 重排序
- [ ] LangSmith span：`retrieve` → `rerank` 分段计时
- [ ] 评测：对比 rerank 前后 MRR

**面试点**：Bi-encoder vs Cross-encoder；为什么重排放检索后面？

---

## Story 4.05 — 多 Query 与 RRF 融合

**目标**：覆盖 **改写问法、中英混问、HyDE 假设文档**。

- [ ] Query 扩展：原 query + LLM 改写 1～2 条（或 HyDE 生成伪答案再 embed）
- [ ] 每路 top_k 召回 → **RRF（Reciprocal Rank Fusion）** 合并
- [ ] 与 Story 4.03 Hybrid 组合：`(vector + bm25) × multi-query` 架构图
- [ ] 配置开关：默认 **关**；仅评测 / 高级 API 参数开启

**面试点**：RRF 公式？为什么比分数加权稳？

---

## Story 4.06 — MMR 多样性（可选）

**目标**：top_k 结果不全是同一球员/同一比赛重复片段。

- [ ] 在向量分数上做 **MMR**：平衡 relevance vs 与已选 chunk 的距离
- [ ] 参数 `lambda` 可配置；世界杯场景默认可关

**面试点**：什么时候需要 MMR？什么时候反而伤害答案？

---

## Story 4.07 — pgvector ANN 索引

**目标**：数据量 / QPS 上升后延迟可控。

- [ ] migration：`HNSW` on `embedding` with `vector_cosine_ops`
- [ ] 压测：~2.2 万 vs 10 万 synthetic 行的 p95 延迟
- [ ] 文档：与 V1 暴力 scan 对比；recall@k 是否下降

**面试点**：IVFFlat vs HNSW；建索引前为何要 `ANALYZE`？

---

## Story 4.08 — 结构化并行检索（进阶，可选）

**目标**：向量找「叙述」，SQL 找「精确统计」—— **Graph RAG  lite**。

- [ ] 示例：query 含「进球数」→ 并行查 `wc_*` 表 + vector search
- [ ] LangGraph `retrieve` 节点：多 tool 结果 merge（与 EP05 衔接）
- [ ] 非 V1 必须；世界杯 Silver 已有时价值高

**面试点**：RAG vs Text2SQL vs 混合编排？

---

## Sandbox 学习（不阻塞主产品）

在 **`ep04-rag` 未 archive 前** 也可做 **只读实验**：

| 实验 | 路径建议 | 产出 |
|:-----|:---------|:-----|
| BM25 + 向量 RRF | `scripts/rag/sandbox_hybrid.py` | 1 页笔记 + 3 query 对比 |
| Cross-encoder rerank | `scripts/rag/sandbox_rerank.py` | latency + MRR 表 |
| RRF 多路 | `scripts/rag/sandbox_rrf.py` | 示意图 |
| P@5 基线 | `scripts/rag/sandbox_eval_baseline.py` | vector vs hybrid 对比 |

运行说明见 [`scripts/rag/README.md`](../../../scripts/rag/README.md)。

---

## 非目标

- 替换 EP04-01 结构化数据或 Gold 事实卡管线
- 上生产必开多路检索（应 **feature flag**）
- 本 epic 内做 PDF 上传解析（见 EP04 Story 4.1–4.2）
- 专用向量库迁移（Milvus/Qdrant）— 除非 PG 压测不达标另开 epic

---

## 建议 OpenSpec 拆分

| Change | 范围 |
|:-------|:-----|
| `ep04-rag-eval` | Story 4.01 评测集 + baseline |
| `ep04-rag-hybrid` | Story 4.03 + 4.05 RRF |
| `ep04-rag-rerank` | Story 4.04 |
| `ep04-rag-ann` | Story 4.07 |

每个 change 独立 Harness；合并进 `feat/ep04-rag-advanced` 集成分支。

---

## 同步学习（补 L03 缺口）

- [ ] 📖 Bi-encoder / Cross-encoder / ColBERT 区别
- [ ] 📖 BM25 原理与中文分词注意点
- [ ] 📖 RRF、MMR、HyDE 各解决什么问题
- [ ] 📖 检索指标：P@k、Recall@k、MRR、nDCG
- [ ] 📖 两阶段检索：recall 阶段宽、precision 阶段窄
- [ ] 🔧 完成 Story 4.01 baseline 报告
- [ ] 🔧 至少实现 **Hybrid 或 Rerank 之一** 并对比 baseline
- [ ] 🔧 面试能画：**多路召回 → 融合 → 重排 → 阈值 → 生成** 数据流图

---

## 变更记录

| 日期 | 说明 |
|:-----|:-----|
| 2026-06-07 | 立项：V1 单向量检索足够产品；本 epic 承载进阶检索学习与后续增强 |
