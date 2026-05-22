# 12 周迭代总览

> 来源：[project-description.md](../project-description.md)  
> 架构：**FastAPI + Next.js** · **LangGraph** · **LangSmith** · **LangChain / LlamaIndex** 双 RAG

## 迭代表

| 迭代 | 周期 | 史诗 | 阶段目标 | 学习路线 |
|:----:|:-----|:-----|:---------|:---------|
| 1 | 第 1-2 周 | EP00 + EP01 + EP03 | 协作栈 + Monorepo + 数据库/缓存 | [L00](./learning/L00-ai-collab-stack.md) + [L01](./learning/L01-foundation.md) |
| 2 | 第 3 周 | EP02 | 流式对话 + LangGraph + LangSmith | [L02](./learning/L02-streaming-langgraph.md) |
| 3 | 第 4-5 周 | EP04 | LangChain 快 RAG + LlamaIndex 自研 RAG | [L03](./learning/L03-rag-dual-stack.md) |
| 4 | 第 6 周 | EP05 | LangGraph Agent 全流程 | [L04](./learning/L04-agent.md) |
| 5 | 第 7 周 | EP06 + EP07 | 记忆体系 + AI 工作流 Demo | [L05](./learning/L05-memory-workflow.md) |
| 6 | 第 8 周 | EP08 | Docker + 腾讯云上线 + CI/CD | [L06](./learning/L06-deployment.md) |
| 7 | 第 9 周 | EP09 | 性能 / 安全 / Token 成本 | [L07](./learning/L07-optimization.md) |
| 8 | 第 10-12 周 | EP10 | 打磨 + 面试素材 | [L08](./learning/L08-interview.md) |

## 开发原则（摘要）

1. **不裸调**复杂业务流程用大模型 API；对话 / Agent / RAG 编排走 **LangGraph**（及配套生态）。
2. **可观测**全流程接 **LangSmith**，线上线下同一套排查方式。
3. **知识库**：快迭代用 **LangChain RAG**；深度定制与 Token 强管控用 **LlamaIndex 自研**。
4. **成本**：切块、拼接、统计三层管控 Token。
5. **协作**：**OpenSpec** 对齐变更 · **Superpowers** 约束 AI 实现 · **Harness** 回归 Agent/API（见 [ai-collab-stack.md](../tech/ai-collab-stack.md)）。

## 周度跟踪（完成度手动更新）

| 周 | 迭代目标 | 完成度 | 本周重点 | 下周计划 | 阻碍 |
|:--:|:---------|:------:|:---------|:---------|:-----|
| 1 | EP01+EP03 启动 | 0% | 前后端空白工程、DB 环境 | 目录分层、基础接口 | |
| 2 | EP01+EP03 收尾 | 0% | 规范、表设计 | 流式对话 | |
| 3 | EP02 | 0% | 聊天 UI、LangGraph、LangSmith | 流式异常、多轮 | |
| 4 | EP04 基础 | 0% | 上传、解析、切块 | Embedding、检索 | |
| 5 | EP04 闭环 | 0% | LlamaIndex、Token 管控 | 溯源、双模式切换 | |
| 6 | EP05 | 0% | 工具、Agent 流程 | 重试、分支 | |
| 7 | EP06+EP07 | 0% | 记忆、工作流 Demo | 压缩、检索优化 | |
| 8 | EP08 | 0% | Docker、Nginx、上线 | CI/CD、线上 BUG | |
| 9 | EP09 | 0% | 限流、缓存、成本 | 架构图 | |
| 10 | EP10 打磨 | 0% | 交互、压测 | 代码清理 | |
| 11 | EP10 面试 | 0% | 架构图、难点总结 | 题库、话术 | |
| 12 | 复盘冲刺 | 0% | 演示、模拟面试 | 简历投递 | |

复盘模板 → [weekly-tracker.md](./weekly-tracker.md)
