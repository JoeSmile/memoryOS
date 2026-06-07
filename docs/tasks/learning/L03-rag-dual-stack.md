# L03 — RAG 双架构（第 4-5 周）

**对应史诗**：EP04  
**架构原则**：快迭代用 LangChain；深度定制 + Token 强管控用 LlamaIndex

---

## 1. 文档摄入与预处理

### 学什么

- [ ] 📖 格式：PDF（版式乱）、MD（结构清）、扫描件需 OCR（可选）
- [ ] 📖 清洗：空白、页眉页脚、乱码、重复页
- [ ] 📖 元数据：`source`、`page`、`uploaded_at` 写入 chunk
- [ ] 📖 大文件：异步任务 + 状态 `pending/processing/ready/failed`
- [ ] 🔧 `services/ingestion/` + 前端上传进度

### 面试常问

- PDF 表格和多栏排版为什么难 RAG？你怎么处理？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 上传未校验 MIME/大小 | 内存打满 | 白名单 + 上限 |
| 同步解析阻塞 API | 超时 504 | 后台任务队列 |
| 编码非 UTF-8 | 乱码入库 | chardet + 转码 |
| 同一文件重复上传 | 向量重复 | 文件 hash 去重 |

---

## 2. 切块（Chunking）

> **项目落地笔记**（方法、坑、面试、实施记录）：[`docs/tech/rag-embedding-chunking.md`](../../tech/rag-embedding-chunking.md)

### 学什么

- [ ] 📖 固定长度 + overlap（512/128 起步调参）
- [ ] 📖 按标题/段落层级切（适合 MD/技术文档）
- [ ] 📖 语义切（成本高，按需）
- [ ] 📖 单 chunk Token 上限（与模型 context 对齐）
- [ ] 📖 父子 chunk：检索子块、上下文带父块（可选）

### 面试常问

- chunk 太大太小分别什么问题？overlap 作用？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 在句号中间切断 | 语义断裂 | 按分隔符 + overlap |
| 无 overlap | 跨块答案丢失 | 10–20% overlap |
| 图表/表格当纯文本 | 检索无意义 | 单独处理或跳过 |

---

## 3. Embedding 与 pgvector

> 同上：[rag-embedding-chunking.md §3–§4](../../tech/rag-embedding-chunking.md)

### 学什么

- [ ] 📖 向量维度与模型绑定（换模型需重嵌）
- [ ] 📖 余弦 / 内积；归一化后内积≈余弦
- [ ] 📖 索引：IVFFlat（快建）/ HNSW（查询稳）；数据量小时可先不索引
- [ ] 📖 批量 embedding、失败重试、速率限制
- [ ] 🔧 `embeddings` 表 + 迁移启用 `vector` 扩展

### 面试常问

- 为什么选 pgvector 而不是专用向量库？何时要上 Milvus/Qdrant？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 查询向量维度和库不一致 | 直接报错 | 模型版本常量单一来源 |
| 全表暴力扫描 | 越慢越贵 | 索引 + `LIMIT` |
| 嵌入与原文不同步 | 删了文档还能检索到 | 级联删除 chunk+vector |

---

## 4. LangChain 快速 RAG

### 学什么

- [ ] 📖 LCEL：`loader → splitter → embed → retriever → prompt → llm`
- [ ] 📖 `RetrievalQA` / 自定义 chain；返回 `source_documents`
- [ ] 📖 适用：Demo、内部工具、需求变化快
- [ ] 🔧 `apps/api/app/rag/langchain_pipeline.py`

### 面试常问

- LangChain 优点缺点？为什么你们还要 LlamaIndex？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 默认 chunk 参数无脑用 | 召回差 | 针对 PDF/MD 分策略 |
| 链路过长难 debug | 不知哪步慢 | LangSmith 分段 + 日志 |
| 版本升级 API 变了 | 全挂 | 锁版本 + 集成测试 |

---

## 5. LlamaIndex 自研 RAG

### 学什么

- [ ] 📖 概念：Document → Node → Index → Retriever → QueryEngine
- [ ] 📖 自定义 `BaseReader` / `TextSplitter`（Token 计数内嵌）
- [ ] 📖 Postprocessor：相似度阈值、重排（Cohere/本地）、MMR
- [ ] 📖 Query 改写（多查询召回合并）
- [ ] 📖 **Token 预算**：检索结果总 Token 上限再拼 prompt
- [ ] 🔧 `apps/api/app/rag/llamaindex_pipeline.py`
- [ ] 🔧 `docs/tech/rag-langchain-vs-llamaindex.md`

### 面试常问

- 如何实现「答案必须带引用」？幻觉如何抑制？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 检索 TopK 过大 | 贵 + 噪声多 | TopK + 分数阈值 |
| 只检索不拒答 | 无关也瞎答 | 低分返回「未找到」 |
| 引用片段过长 | 超 context | 引用截断 + 链接详情页 |

---

## 6. 双模式切换与溯源

### 学什么

- [ ] 📖 API 参数：`rag_backend=langchain|llamaindex`
- [ ] 📖 响应结构：`answer` + `citations[{doc, page, snippet}]`
- [ ] 📖 前端引用 UI：脚注/折叠来源
- [ ] 🔧 知识库设置页切换 + 标识当前模式

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 两种 pipeline 响应格式不一 | 前端解析崩 | 统一 DTO |
| 切换后端未清缓存 | 旧策略结果 | 模式写入请求级 config |

---

## 7. RAG 调优清单（面试高频）

| 症状 | 可能原因 | 手段 |
|:-----|:---------|:-----|
| 召回为空 | 切块太大/嵌入差/过滤太严 | 调 chunk、换模型、降阈值 |
| 答非所问 | 召回噪声 | 重排、MMR、压缩 |
| 幻觉严重 | 无引用约束 | 强制仅依据 context、低温 |
| 慢 | 嵌入/检索/生成分段 | LangSmith 看 span |
| 贵 | context 过长 | Token 预算、摘要 |

- [ ] 🔧 记录 1 次「优化前后」对比到 tech 文档

---

## 7.5 检索进阶（EP04-03 · sandbox 实验）

> V1 `ep04-rag` 只有 **单向量余弦 + collection 过滤**。下面整块在主线用不到，但 **面试必问** — 详见 [EP04-03-rag-retrieval-advanced](../epics/EP04-03-rag-retrieval-advanced.md)。

### 学什么

- [ ] 📖 **Hybrid**：BM25/FTS + 向量；何时补专有名词与数字
- [ ] 📖 **RRF**：多路 rank 融合（向量路 + 关键词路 + 多 query 路）
- [ ] 📖 **Rerank**：cross-encoder 二阶段；top_20 → top_5
- [ ] 📖 **Query 扩展 / HyDE**：改写问法、假设文档 embedding
- [ ] 📖 **MMR**：结果多样性 vs 相关性
- [ ] 📖 **指标**：P@k、Recall@k、MRR、nDCG；固定 20～50 条评测集
- [ ] 🔧 sandbox：`scripts/rag/sandbox_*.py` 任完成 **1 项** 并写对比表
- [ ] 🔧 `docs/tech/rag-retrieval-advanced.md` baseline 数字（Story 4.01 后）

### 面试常问

- 召回不准时你的排查顺序？单向量 vs Hybrid vs 重排各解决什么？
- 为什么生产上多路检索常默认 **关**，用 feature flag 开？

---

## 8. LangSmith 观测 RAG

- [ ] 📖 分段：ingest / embed / retrieve / synthesize 耗时
- [ ] 🔧 保存 1 份慢查询 trace 分析（截图 + 文字）

## 阶段自测

- [ ] 能画双 pipeline 对比图 + 选型话术  
- [ ] 口述：切片 → 检索 → Prompt → 生成 各可能故障点  
- [ ] Demo：同一问题切换两种后端（可选）
