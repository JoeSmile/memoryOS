# RAG retrieval sandbox（EP04-03 学习区）

离线实验脚本：**不接入** `POST /knowledge/search`，不影响 `ep04-rag` V1 主链路。

## 前置

- 仓库根目录执行
- 使用 `apps/api` 的 Python 环境（mock embedding，无需 API Key / DB ingest）

```bash
# 在仓库根目录
bash scripts/api.sh exec python ../../scripts/rag/sandbox_hybrid.py \
  --query "1930 France Mexico 4-1"
```

## 脚本

| 文件 | 练什么 | 对应 Story |
|:-----|:-------|:-----------|
| `sandbox_hybrid.py` | 向量 vs 关键词 vs RRF 融合 | 4.03 |
| `sandbox_rrf.py` | 多 query 列表 + RRF | 4.05 |
| `sandbox_rerank.py` | 两阶段 recall → rerank（stub CE） | 4.04 |
| `sandbox_eval_baseline.py` | P@5 基线（`--mode vector\|hybrid`） | 4.01 |
| `eval_queries.yaml` | 固定评测 query（可扩展） | 4.01 |

## 面试话术（脚本跑完能讲）

1. **为什么 Hybrid？** 向量擅语义；比分、日期、专名用关键词路补精确匹配。
2. **RRF 是什么？** 多路 rank 融合，不依赖分数尺度：`1/(k+rank)`。
3. **Rerank 放哪？** 先 bi-encoder 宽召回，再 cross-encoder 窄精排。
4. **和 collection 过滤？** 过滤是 metadata 预筛；Hybrid 是多路召回融合，正交能力。

## 下一步（自己扩展）

- [ ] 将 `keyword_rank` 换成 Postgres `tsvector` 或 `rank_bm25`
- [ ] 将 `vector_rank` 换成 DB `search_similar` + live embed
- [ ] 将 stub rerank 换成真实 cross-encoder / Cohere rerank
- [ ] 结果写入 [`docs/tech/rag-retrieval-advanced.md`](../../docs/tech/rag-retrieval-advanced.md) §8

详见 [EP04-03 史诗](../../docs/tasks/epics/EP04-03-rag-retrieval-advanced.md) 与 **[检索进阶文档](../../docs/tech/rag-retrieval-advanced.md)**（各方法说明与面试对照）。
