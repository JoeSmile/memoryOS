# MemoryOS 任务与学习管理中心

> 基于 [项目总览](../project-description.md) 拆分的**开发任务**与**同步学习路线**。  
> 原则：**边做边学**，学完必在仓库里留下代码或文档痕迹。

## 快速导航

| 类型 | 文档 |
|:-----|:-----|
| 12 周总览 | [00-iteration-overview.md](./00-iteration-overview.md) |
| MVP 后演进 | [post-mvp-roadmap.md](./post-mvp-roadmap.md) |
| AI 协作栈（Collab） | [EP00](./epics/EP00-ai-collaboration.md) · [L00](./learning/L00-ai-collab-stack.md) · [最佳实践](../tech/ai-collab-best-practices.md) · [团队 onboarding](../team/onboarding.md) |
| 周度复盘模板 | [weekly-tracker.md](./weekly-tracker.md) |
| 双轨进度看板 | [progress-dashboard.md](./progress-dashboard.md) |
| 学习路线索引 | [learning/README.md](./learning/README.md) |

### 史诗任务（开发）

| 史诗 | 周期 | 任务文件 | 学习路线 |
|:----:|:-----|:---------|:---------|
| EP00 | 贯穿 | [epics/EP00-ai-collaboration.md](./epics/EP00-ai-collaboration.md) | [L00 协作栈](./learning/L00-ai-collab-stack.md) |
| EP01 | 1-2 周 | [epics/EP01-engineering.md](./epics/EP01-engineering.md) | [L01 基建](./learning/L01-foundation.md) |
| EP03 | 1-2 周并行 | [epics/EP03-data-storage.md](./epics/EP03-data-storage.md) | [L01 基建](./learning/L01-foundation.md) |
| EP02 | 第 3 周 | [epics/EP02-streaming-chat.md](./epics/EP02-streaming-chat.md) | [L02 流式+LangGraph](./learning/L02-streaming-langgraph.md) |
| EP04 | 4-5 周 | [epics/EP04-rag.md](./epics/EP04-rag.md) | [L03 RAG 双架构](./learning/L03-rag-dual-stack.md) |
| EP04-01 | EP04 第 1 周 | [epics/EP04-01-worldcup-data-etl.md](./epics/EP04-01-worldcup-data-etl.md) | L03 §1 · 结构化 ETL |
| EP04-02 | **上线后** | [epics/EP04-02-wiki-crawl.md](./epics/EP04-02-wiki-crawl.md) 📋 已立项暂缓 | L03 · Wiki 补充 RAG |
| EP04-03 | **`ep04-rag` 后** | [epics/EP04-03-rag-retrieval-advanced.md](./epics/EP04-03-rag-retrieval-advanced.md) 📋 已立项暂缓 | L03 §7.5 · Hybrid/重排/RRF |
| EP05 | 第 6 周 | [epics/EP05-agent.md](./epics/EP05-agent.md) | [L04 Agent](./learning/L04-agent.md) |
| EP06 | 第 7 周 | [epics/EP06-memory.md](./epics/EP06-memory.md) | [L05 记忆+工作流](./learning/L05-memory-workflow.md) |
| EP07 | 第 7 周 | [epics/EP07-workflow.md](./epics/EP07-workflow.md) | [L05 记忆+工作流](./learning/L05-memory-workflow.md) |
| EP08 | 第 8 周 | [epics/EP08-deployment.md](./epics/EP08-deployment.md) | [L06 部署](./learning/L06-deployment.md) |
| EP09 | 第 9 周 | [epics/EP09-optimization.md](./epics/EP09-optimization.md) | [L07 优化安全](./learning/L07-optimization.md) |
| EP10 | 10-12 周 | [epics/EP10-polish.md](./epics/EP10-polish.md) | [L08 面试冲刺](./learning/L08-interview.md) |
| EP11 | MVP 后 backlog | [epics/EP11-memory-ops.md](./epics/EP11-memory-ops.md) | EP06 企业级补强：队列 / 溯源 / 监控 |
| EP12 | MVP 后 backlog | [epics/EP12-memory-eval.md](./epics/EP12-memory-eval.md) | EP06 企业级补强：记忆质量评测 |
| EP13 | MVP 后 backlog | [epics/EP13-memory-distributed.md](./epics/EP13-memory-distributed.md) | [L09 分布式](./learning/L09-distributed-orchestration.md) · Remote 热插拔 |
| EP14 | MVP 后 backlog | [epics/EP14-k8s-cloud.md](./epics/EP14-k8s-cloud.md) | L09 · K8s / 腾讯云 TKE |

### 技术文档（随开发沉淀，待你创建）

| 文档 | 状态 | 触发史诗 |
|:-----|:----:|:---------|
| [FE-engineering.md](../tech/FE-engineering.md) | ✅ 已有 | EP01 |
| `docs/tech/BE-engineering.md` | 📋 待写 | EP01 / EP03 |
| [langgraph-chat.md](../tech/langgraph-chat.md) | ✅ 已有 | EP02 |
| [chat-stream-cancel.md](../tech/chat-stream-cancel.md) | ✅ 已有 | EP02 · Stop/Cancel |
| `docs/tech/rag-langchain-vs-llamaindex.md` | 📋 待写 | EP04 |
| `docs/tech/rag-retrieval-advanced.md` | ✅ 已有 | EP04-03 · sandbox 方法说明 |
| `docs/tech/agent-langgraph.md` | 📋 待写 | EP05 |
| `docs/tech/memory-system.md` | 📋 待写 | EP06 · EP11 运维章节 |
| `docs/tech/memory-eval.md` | 📋 待写 | EP12 |
| `docs/tech/distributed-orchestration.md` | 📋 待写 | EP13 |
| `docs/tech/k8s-tencent-deploy.md` | 📋 待写 | EP14 |
| `docs/architecture/distributed-hotplug.md` | 📋 待写 | EP13 |
| `docs/architecture/*.md` | 📋 待写 | EP08 / EP09 |

---

## 如何使用（勾选跟踪）

1. 开发任务：打开 `epics/*.md`，完成后将 `- [ ]` 改为 `- [x]`。
2. 学习项：在 `learning/*.md` 中单独勾选，区分 **已学（📖）** 与 **已落地（🔧）**（见各学习文件说明）。
3. 每周日复制 [weekly-tracker.md](./weekly-tracker.md) 做复盘，并更新 [progress-dashboard.md](./progress-dashboard.md)。

---

## 双轨进度管理建议（开发 + 学习）

### 1. 两条轨道，不要混为一谈

| 轨道 | 衡量什么 | 记录在哪 |
|:-----|:---------|:---------|
| **Build 轨** | 功能是否可用、能否演示 | `epics/*.md` 任务勾选 |
| **Learn 轨** | 是否理解原理、能否讲清楚 | `learning/*.md` + 自写 `docs/tech/*` |
| **Collab 轨** | 需求可追溯、AI 可控、可回归 | [EP00](./epics/EP00-ai-collaboration.md) + OpenSpec + Harness |

**建议比例（按周）**：约 **65% Build / 25% Learn / 10% Collab**（第 1 周 Collab 可提到 20%，完成 EP00 0.1–0.2）。遇到阻塞再临时加大学习比重，避免「只看不写」。

### 2. 每条学习项设两个勾

在学习文件中使用：

- `[ ]` **理解**：能用自己的话解释或画简图  
- `[x]` **落地**：仓库里有对应 PR / 文件 / 配置（注明路径）

示例：`LangGraph State` — 理解 ✅ + 落地 `apps/api/app/graphs/chat.py` ✅

### 3. 固定周节奏（推荐）

| 日 | 动作 |
|:---|:-----|
| 周一 | 看 `00-iteration-overview.md`，定本周 3～5 个 **Build** 任务 |
| 周二～五 | 先完成最小可运行切片，再补学习笔记 |
| 周六 | 补 1 篇短文档（`docs/tech/` 几百字即可） |
| 周日 | 填 `weekly-tracker.md`，更新 `progress-dashboard.md` 完成度 |

### 4. 文档即学习成果

每完成一个史诗，至少产出 **一篇** 技术文档（可很短）：

- 解决了什么问题  
- 关键代码在哪  
- 踩坑与备选方案  

这样 EP10 面试素材直接从 `docs/tech/` 拼装，不用临阵磨枪。

### 5. 框架类技术（LangGraph / LangSmith / LlamaIndex）的学习顺序

```
先官方 Quickstart（本地跑通）
  → 接入 MemoryOS 最小链路（一个接口）
    → LangSmith 打开 trace 对照代码
      → 再扩展节点 / 双 RAG / Agent
```

避免在业务代码里第一次试错；用 **sandbox 脚本** 或 `apps/api/scripts/` 做实验。

### 6. 进度可视化（三选一即可）

| 方式 | 适合 | 说明 |
|:-----|:-----|:-----|
| **本仓库 Markdown** | 个人 / 开源 | `progress-dashboard.md` + 勾选，零成本 |
| **GitHub Projects** | 要远程协作 | 把 epic 标题建成 Issue / Project 列 |
| **Notion / 飞书多维表** | 要统计学时 | 字段：史诗 / 任务 / 学习主题 / 状态 / 文档链接 |

不必三套同时维护，**以 `docs/tasks` 为唯一真相源**，其他只做镜像。

### 7. 防崩盘规则

- 单周 Build 任务不超过 **5 条**「完成定义清晰」项。  
- 学习路线允许 **延后**，但 Build 的 P0 不能跨周堆积超过 2 项。  
- 连续 2 天卡住 → 缩小范围（例如先裸 SSE，再上 LangGraph）。  
- EP07（P2）时间不够可整史诗后移，保 EP02 / EP04 / EP08。
- **分布式 / Remote 热插拔 / K8s**：MVP 后按 [post-mvp-roadmap.md](./post-mvp-roadmap.md) 做 EP11–EP14，**勿在 EP02–EP08 中途改主编排架构**。

---

## 当前进度快照

| 史诗 | Build 进度 | 说明 |
|:-----|:-----------|:-----|
| EP00 | 🟡 进行中 | Superpowers / OpenSpec / Harness 已入文档，待本机 init |
| EP01 | 🟡 进行中 | Story 1.1–1.4 已完成，1.5 可选 |
| EP03 | ⚪ 未开始 | 建议先 EP00 0.1–0.2 + propose ep03 |
| 其余 | ⚪ 未开始 | — |

详细勾选见各 `epics/*.md` 与 [progress-dashboard.md](./progress-dashboard.md)。
