# EP04 — RAG 知识库（双架构）

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 4-5 周 |
| **优先级** | P0 |
| **依赖** | EP02、EP03、**[EP04-01 世界杯 CSV ETL](./EP04-01-worldcup-data-etl.md)** ✅（Silver + Gold 事实卡已就绪） |
| **学习路线** | [L03-rag-dual-stack.md](../learning/L03-rag-dual-stack.md) |
| **目标文档** | [`rag-embedding-chunking.md`](../../tech/rag-embedding-chunking.md) ✅ · [`chat-rag-stream.md`](../../tech/chat-rag-stream.md) 📋（BFF 结构化溯源升级） · `rag-langchain-vs-llamaindex.md` 📋 |

> **世界杯 30 CSV**：清洗与规范化见子史诗 [EP04-01](./EP04-01-worldcup-data-etl.md)；EP04 消费其 **Gold 事实卡**，不直接吃原始 CSV。

---

## Story 4.1 前端上传

- [ ] 知识库页 `/knowledge`
- [ ] PDF/MD 上传、进度、校验、列表与删除

## Story 4.2 文档解析

- [ ] 多格式解析、清洗、元数据
- [ ] 异步任务（BackgroundTasks / 队列）

## Story 4.3 切块策略

- [ ] 固定长度、语义、层级标题切块（PDF/MD · Story 4.2 排期）
- [x] `document_chunks` 表（Gold **路径 A**：一卡一块 · `ep04-rag` ✅）

## Story 4.4 LangChain 快速 RAG

- [x] 轻量化 RAG Pipeline（**首 slice**：Gold ingest → embed → `POST /knowledge/search`；**不含**生成 · `ep04-rag` ✅）
- [x] 满足快速问答与 Demo（LangGraph retrieve + chat SSE · `ep04-rag-chat` ✅）

## Story 4.5 LlamaIndex 自研体系

- [ ] 自定义 Document Loader、Splitter（非默认）
- [ ] 自主 Embedding 管理 + pgvector 入库
- [ ] 召回、TopK、重排、Query 改写
- [ ] **内置 Token 统计**：切块与上下文长度强制上限

## Story 4.6 对话与溯源

- [x] RAG Prompt 模板（`ep04-rag-chat` ✅）
- [x] 答案引用来源（V1 Markdown 脚注 · `ep04-rag-chat` ✅；**structured chips** 见 [`chat-rag-stream.md`](../../tech/chat-rag-stream.md)）
- [x] 无命中兜底策略（`ep04-rag-chat` ✅）

## Story 4.7 维护与双模式

- [ ] 增量更新、删除同步、切片去重
- [ ] API / 配置：**LangChain 模式 ↔ LlamaIndex 模式** 切换
- [ ] LangSmith 观测 RAG 各阶段耗时

---

## 上线后增强（已立项，不做进当前 change）

| 子项 | 文档 | 门禁 |
|:-----|:-----|:-----|
| Wikipedia 爬虫补充 RAG | [EP04-02-wiki-crawl](./EP04-02-wiki-crawl.md) | **EP08 上线后**再 propose/实现 |
| Hybrid / 重排 / 多路召回 | [EP04-03-rag-retrieval-advanced](./EP04-03-rag-retrieval-advanced.md) | **`ep04-rag` archive 后**；V1 仅单向量余弦 |

---

## 同步学习

- [ ] 文档解析与预处理（理解 / 落地）
- [ ] Embedding 与相似度（理解 / 落地）
- [ ] LangChain RAG 流程与优缺点（理解 / 落地）
- [ ] LlamaIndex 存储/索引/检索/查询层（理解 / 落地）
- [ ] 召回不准、幻觉、冗余上下文优化（理解）
- [ ] LangSmith 定位 RAG 瓶颈（理解 / 落地）
