# 同步学习路线索引

> 与 [project-description.md](../../project-description.md) 对齐。  
> 每阶段除「学什么」外，均含 **面试常问**、**实战易踩坑**（坑表），踩坑亦需 📖 理解 + 遇过或 🔧 记录对策。

## 如何使用

| 标记 | 含义 |
|:----:|:-----|
| 📖 | 能讲解原理、能答面试追问 |
| 🔧 | 仓库有代码/配置/文档（weekly 复盘写路径） |

- 任务项 `- [ ]`：建议至少完成 📖；核心项再 🔧。
- **坑表**：不要求全踩一遍，但每条应能说出「现象 → 规避」；踩过的写入 `docs/tech/challenges.md` 或当周 retro。

## 文档结构（每个 L*.md）

```
学什么（细分勾选）
  ↓
面试常问（口述练习）
  ↓
实战易踩坑（表格：坑 | 现象 | 规避）
  ↓
阶段自测
```

## 阶段与周次

| 文件 | 周次 | 史诗 | 体量 |
|:-----|:-----|:-----|:-----|
| [L00-ai-collab-stack.md](./L00-ai-collab-stack.md) | 1 起贯穿 | EP00 | Superpowers · OpenSpec · Harness |
| [L01-foundation.md](./L01-foundation.md) | 1-2 | EP01 + EP03 | 基建 + DB + JWT |
| [L02-streaming-langgraph.md](./L02-streaming-langgraph.md) | 3 | EP02 | SSE + LangGraph |
| [L03-rag-dual-stack.md](./L03-rag-dual-stack.md) | 4-5 | EP04 | 双 RAG |
| [L04-agent.md](./L04-agent.md) | 6 | EP05 | Agent 工具 |
| [L05-memory-workflow.md](./L05-memory-workflow.md) | 7 | EP06 + EP07 | 记忆 + 工作流 |
| [L06-deployment.md](./L06-deployment.md) | 8 | EP08 | Docker + CI |
| [L07-optimization.md](./L07-optimization.md) | 9 | EP09 | 安全 + 成本 |
| [L08-interview.md](./L08-interview.md) | 10-12 | EP10 | 面试冲刺 |

## 知识笔记（深读）

| 笔记 | 阶段 |
|:-----|:-----|
| [nextjs15.md](../../tech/knowledge/nextjs15.md) | L01、L02 |
| [vite-vs-turbopack.md](../../tech/knowledge/vite-vs-turbopack.md) | L01 |
| [FE-engineering.md](../../tech/FE-engineering.md) | L01 |

## 官方文档

| 主题 | 链接 |
|:-----|:-----|
| Next.js | https://nextjs.org/docs |
| FastAPI | https://fastapi.tiangolo.com |
| OpenSpec | https://openspec.dev/ |
| Superpowers | https://github.com/obra/superpowers |
| LangGraph | https://langchain-ai.github.io/langgraph/ |
| LangSmith | https://docs.smith.langchain.com |
| LlamaIndex | https://docs.llamaindex.ai |
| pgvector | https://github.com/pgvector/pgvector |

## 建议产出

每阶段结束：**1 篇 tech 文档** + **≥2 条踩坑记录** → 见 [tasks/README.md](../README.md)
