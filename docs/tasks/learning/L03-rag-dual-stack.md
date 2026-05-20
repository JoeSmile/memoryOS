# L03 — RAG 双架构（第 4-5 周）

**对应史诗**：EP04

---

## 1. 文档与预处理

- [ ] 📖 PDF/MD 解析库选型与局限
- [ ] 📖 清洗：页眉页脚、空白、编码
- [ ] 🔧 落地：`apps/api/app/services/ingestion/`

## 2. Embedding 基础

- [ ] 📖 向量维度、余弦相似度、归一化
- [ ] 📖 pgvector 索引类型（IVFFlat / HNSW）选型
- [ ] 🔧 落地：向量表 + 入库脚本

## 3. LangChain RAG（快速版）

- [ ] 📖 LCEL / Runnable 链式组成
- [ ] 📖 优点：快；缺点：定制与 Token 管控弱
- [ ] 🔧 落地：`apps/api/app/rag/langchain_pipeline.py`
- [ ] 🔧 对比记录进 `docs/tech/rag-langchain-vs-llamaindex.md`

## 4. LlamaIndex 自研（深度版）

- [ ] 📖 Document、Node、Index、Retriever、QueryEngine
- [ ] 📖 自定义 Loader / Splitter
- [ ] 📖 Postprocessor 重排、Query 改写
- [ ] 📖 **Token 计数**嵌入切块与检索链路
- [ ] 🔧 落地：`apps/api/app/rag/llamaindex_pipeline.py`

## 5. RAG 调优

- [ ] 📖 召回不准：chunk 大小、overlap、混合检索
- [ ] 📖 幻觉：引用强制、温度、拒答策略
- [ ] 📖 冗余：TopK、MMR、上下文预算
- [ ] 🔧 落地：双模式切换 API + 前端标识当前模式

## 6. LangSmith 观测 RAG

- [ ] 📖 分段耗时：解析 / embed / retrieve / generate
- [ ] 🔧 落地：一次慢查询的 trace 分析与优化记录

---

## 面试话术预备（可先记提纲）

- 何时 LangChain vs LlamaIndex（见 project-description 准则 1、4）  
- 线上问题分层：切片 → 检索 → Prompt → 模型
