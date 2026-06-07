# RAG 切块与 Embedding 实战笔记（MemoryOS）

> **用途**：EP04 实施与面试共用。实施 `ep04-rag` 时在 **写 EmbeddingService / 摄入代码前后** 与本节对照，把最终决策填入 [§6 实施记录](#6-实施记录)。  
> **关联**：[L03 学习路线](../tasks/learning/L03-rag-dual-stack.md) · [EP04 史诗](../tasks/epics/EP04-rag.md) · [worldcup Gold README](../../data/gold/worldcup/README.md)

---

## 1. 两条数据路径（先分清再选策略）

| 路径 | 来源 | 切块 | 典型场景 |
|:-----|:-----|:-----|:---------|
| **A. 预格式化事实卡** | EP04-01 Gold `*.jsonl` | **无需二次切块**（一行 = 一条语义完整的 `text`） | 世界杯结构化数据 → RAG |
| **B. 原始文档** | 用户 PDF/MD（Story 4.2，暂未排期） | **必须切块**（固定长 / 标题 / 语义） | 通用知识库 |

**V1（`ep04-rag`）只走路径 A。** 路径 B 的策略在本文 §3 先写通用方法论，实施留到上传解析 change。

---

## 2. 切块（Chunking）

### 2.1 为什么要切块

1. **嵌入模型有最大输入长度**（通常 512–8192 token）；超长文本不能整篇 embed 一次。  
2. **检索粒度**：整本书一个向量 → 只能匹配「像不像整本书」，无法定位到「梅西 2022 进了几球」。  
3. **生成 context 有上限**：即使检索到了，拼进 prompt 的总量仍受 LLM context 限制。

### 2.2 策略对比（路径 B 用；面试常问）

| 策略 | 做法 | 优点 | 缺点 |
|:-----|:-----|:-----|:-----|
| **固定长度 + overlap** | 如 512 token，overlap 128 | 简单、可预测 | 易在句中切断 |
| **分隔符感知** | 先按 `\n\n`、句号切，再合并到上限 | 语义边界较好 | 需调分隔符列表 |
| **标题/层级** | Markdown `#` / PDF 大纲 | 技术文档效果好 | 依赖结构 |
| **语义切分** | embedding 相邻句相似度突变处下刀 | 块内语义纯 | 慢、贵 |
| **父子块** | 小子块检索，命中后带父块进 context | 检索准 + 上下文足 | 存储与逻辑复杂 |

### 2.3 参数经验（路径 B 起步）

- **Chunk size**：512 token 附近起步；问答型偏小（256–512），叙述型偏大（512–1024）。  
- **Overlap**：chunk 长度的 **10–20%**；防止答案横跨两块边界时两边都搜不到。  
- **单 chunk 上限**：不超过嵌入模型 max input，且留余量（勿顶满 8192）。

### 2.4 路径 A：Gold JSONL（本项目 V1）

```json
{"id": "player_career:P-14758", "entity_type": "player_career", "text": "[Player Career] Lionel Messi · ..."}
```

- **决策**：`text` 已是 ETL 阶段写好的摘要 → `chunk_index = 0`，**一块一卡**。  
- **collection**：`worldcup-{文件名 stem}`，与 `external_id = id` 幂等 upsert。  
- **注意**：`players.jsonl` 与 `player_careers.jsonl` **并存**（基础 vs  enriched）；检索不限 collection 时可能双命中，调用方可用 `collection` 过滤或后续默认只查 `worldcup-player-careers`。

### 2.5 切块踩坑清单

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 句中切断 | 半句话在一个 chunk | 分隔符优先 + overlap |
| 无 overlap | 「上一句在块 A、下一句在块 B」问法漏召回 | 10–20% overlap |
| chunk 过大 | 向量「平均化」，细节被稀释 | 按实体/段落切（事实卡已解决） |
| chunk 过小 | 上下文不足，生成缺背景 | 父子块或增大 chunk |
| 表格/图表当纯文本 | 检索无意义 | 单独结构化或 OCR 后模板化 |
| 元数据未入库 | 无法按来源过滤/溯源 | `documents` 存 `entity_type`、`source_ids` |
| 重复摄入 | 同 `collection+external_id` 双份 | upsert + 删旧 chunk 再写 embedding |

---

## 3. Embedding

### 3.1 本质

把文本映射为 **固定维度** 的浮点向量，使得语义相近的文本 **距离更近**（通常用余弦相似度或 L2）。

### 3.2 模型与维度绑定（硬约束）

- **换模型 ≈ 必须全量 re-embed**（维度、空间分布都不同）。  
- **单一真相源**：`Settings.embedding_model` + `embedding_dimensions` + Alembic `vector(N)` **必须一致**。  
- OpenAI `text-embedding-3-small` 支持 `dimensions=384` 降维，便于与 mock 维度对齐。

### 3.3 Mock vs Live（MemoryOS 双模式）

| 模式 | 条件 | 用途 |
|:-----|:-----|:-----|
| **Mock** | 无 `OPENAI_API_KEY`（Harness/CI） | 契约测试；**确定性** hash → 384 维 + L2 归一化 |
| **Live** | 有 Key（DashScope OpenAI 兼容） | **本地默认**：全量 ingest、调 TopK/召回准确率 |

**人审决策（2026-06-03）**：本地开发对接 **真实 embedding API**；不用 mock 做语义验证。Mock 仅服务 CI。

**注意**：Mock 向量 **不反映真实语义**；全量数据 + live embed 才便于定位「查不准」是数据、切块还是模型问题。

### 3.4 批量与速率

- 全量 ~2.2 万条：宜 **batch**（如 32–100 条/批），批间 sleep 防 rate limit。  
- 失败策略：**单条重试 3 次** → 记录失败 id → 摄入 exit 非 0 或 partial 报告（实施时二选一，记入 §6）。  
- **幂等**：re-ingest 时先删旧 chunk 再 embed，避免双份向量。

### 3.5 归一化与距离算子

- 若向量 **L2 归一化**，余弦距离与内积排序等价。  
- pgvector：`<=>` cosine distance，`<->` L2；查询与建索引时 **ops 类要一致**（`vector_cosine_ops`）。

### 3.6 Embedding 踩坑清单

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 维度不一致 | insert/search 直接报错 | 模型常量 + migration 版本化 |
| 查询用错模型 | 召回随机 | query 与库用同一 `EmbeddingService` |
| Mock 上生产 | 检索结果无意义 | 环境变量区分；文档标明 |
| 未归一化 + 错用内积 | 排序偏差 | 统一归一化或统一 cosine |
| 全表扫 | 数据量大后变慢 | 见 §4 索引策略 |
| 嵌入与原文不同步 | 删文档仍能搜到 | FK CASCADE + 摄入 replace 策略 |
| 中文/英文混用同一模型 | 个别语种召回差 | 选多语模型（如 text-embedding-3-small 多语尚可） |

### 3.8 本地 Ollama（可选，非 V1）

**问题**：本地起 [Ollama](https://ollama.com) 做 embedding + LLM，效果是否更好？

| 维度 | 云 API（DashScope 等） | 本地 Ollama |
|:-----|:-----------------------|:------------|
| **成本/隐私** | 按量计费；数据出网 | 免费推理；数据不出本机 |
| **Embedding 质量** | `text-embedding-3-small` 等多语稳定 | `nomic-embed-text`、`mxbai-embed-large` 等；英文为主时尚可，**中英混排事实卡需实测** |
| **LLM 质量** | `qwen-turbo` 等商用模型 | 7B–14B 本地模型推理快但世界杯细节/数字 **易弱于** 云端大模型 |
| **运维** | 配 Key 即可 | 需 RAM/VRAM（embed ~1GB，LLM 8B 常需 8GB+）；模型拉取与版本 |
| **与 MemoryOS 集成** | 已有 `OPENAI_BASE_URL` + Key | 可设 `OPENAI_BASE_URL=http://127.0.0.1:11434/v1`（Ollama OpenAI 兼容）；**embedding 模型名需与 chat 分开配置**（V1 未做） |

**结论（V1）**：

- **Embedding**：全量入库 + 调召回，优先 **真实云 embedding**（你已选 A）；语义质量通常优于小参本地 embed，且与现有 DashScope 配置一致。
- **LLM**：本 change **不接聊天**（C）；Ollama LLM 留到接入 LangGraph/RAG 生成时再评估。
- **Ollama 适合**：无外网、强隐私、愿意用更大本地模型（如 `qwen2.5:14b`）并接受调参成本时，可作为 **V2 可选后端**（`embedding_base_url` / `llm_base_url` 分离）。

### 3.7 面试话术（精简）

- **为什么 pgvector 不单独上 Milvus？** 万级 chunk、与业务 PG 同事务、运维简单；千万级或纯向量 SLA 再拆。  
- **换 embedding 模型怎么办？** 新 migration 维度 / 新列或新表 → 后台 re-embed job → 切流量。  
- **Mock embedding 测什么？** 管线、幂等、API 契约；不测语义质量。

---

## 4. pgvector 存储与检索

### 4.1 表设计（V1）

- `documents`：逻辑文档 + `(collection, external_id)` 唯一。  
- `document_chunks`：`content` + `embedding vector(384)` + `chunk_index`。

### 4.2 何时建 ANN 索引

| 规模 | 建议 |
|:-----|:-----|
| &lt; 1 万行 | 可先 **不建** IVFFlat/HNSW，暴力 scan + `LIMIT` 够用 |
| 1 万–百万 | **HNSW**（查询稳）或 **IVFFlat**（建得快，需 `lists` 调参） |
| 换距离算子 | 索引必须 drop 重建 |

V1 ~2.2 万：实施时讨论是否在 `011` 后加 HNSW，或留到数据量/延迟不达标再加（记入 §6）。

### 4.3 检索参数

- **top_k**：5–10 起步；过大 → 噪声多、prompt 贵。  
- **collection 过滤**：世界杯场景强烈建议 API 支持，避免 `players`/`player_careers` 重复。  
- **分数阈值**（后续）：低于阈值返回「未找到」，防幻觉（Story 4.6）。

---

## 5. 实施前讨论清单（与 AI/同伴过一遍）

实施 task 2.x / 3.x 前，逐项定案并写入 §6：

1. **Embedding**：Mock 384 是否足够本阶段？本地全量 ingest 是否必须 Live？  
2. **批量大小与失败策略**：批大小、重试、partial fail 是否允许？  
3. **players + player_careers**：search 默认是否限 `worldcup-player-careers`？  
4. **samples.jsonl**：全量摄入是否保留（与主库内容重叠但 collection 独立）？  
5. **pgvector 索引**：V1 是否加 HNSW？  
6. **距离度量**：cosine + 归一化是否全员统一？  
7. **re-ingest**：删 chunk 再 insert vs upsert embedding——选哪种？

---

## 6. 实施记录

> **规则**：`ep04-rag` 落地 Embedding / Ingest 时 **必填**；archive 前 §6 不能留空 TODO。

| 项 | 决策 | 日期 | 备注 |
|:---|:-----|:-----|:-----|
| embedding 维度 | `384`（`text-embedding-3-small` dimensions 参数） | 2026-06-03 | 实施时确认 migration |
| mock vs live | **本地 live API**；CI/Harness mock | 2026-06-03 | 人审 A |
| 摄入范围 | **全量 5 jsonl**（含 players + player_careers） | 2026-06-03 | 人审 B |
| 聊天集成 | **本 change 不做** | 2026-06-03 | 人审 C |
| Ollama | **V1 不接入**；V2 可选本地后端 | 2026-06-03 | 见 §3.8 |
| re-ingest `updated_at` | `DocumentRepository.upsert` + `touch_updated_at` | 2026-06-07 | code review P1 |
| 维度单一来源 | `app/core/rag_constants.py` + `Settings.embedding_dimensions` | 2026-06-07 | code review P2 |
| 批量 embed batch size | — | — | 待 task 2.1 填 |
| 失败重试策略 | — | — | 待 task 2.1 填 |
| search 默认 collection | `null`（不限，全库搜） | 2026-06-03 | 人审 B；可按需传 collection |
| V1 是否 HNSW | **否**（~2.2 万行先暴力 scan + LIMIT） | 2026-06-07 | task 1.2 |
| 全量 ingest 行数验收 | 预期 ~22090 | — | 待 task 3.3 跑完填实际数 |

### 6.1 实施后复盘（可选）

- [ ] 用 3 个固定 query 对比 mock vs live Top3（若有 Key）  
- [ ] 记录 1 条「踩坑 → 修复」到上表或 L03

---

## 7. 变更记录

| 日期 | 说明 |
|:-----|:-----|
| 2026-06-03 | 初稿：路径 A/B、切块/embedding/pgvector 坑表、实施讨论清单（ep04-rag propose） |
