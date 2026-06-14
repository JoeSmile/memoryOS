# MVP 后演进路线（记忆企业级 + 分布式编排）

> **原则**：12 周主排期（EP00–EP10）专注 **可演示 MVP**（单机 Docker + 腾讯云轻量部署）；**不**在 EP02–EP08 中途改成微内核/注册中心架构。  
> 分布式与 Remote Agent 热插拔作为 **MVP 后 backlog**，按依赖顺序增量落地。

## 为什么 MVP 后再改架构？

| 若现在改 EP02–EP07 | 风险 |
|:-------------------|:-----|
| 主编排 + 注册中心 + 多 RemoteGraph | OpenSpec/Harness 全面返工，SSE/记忆/RAG 回归面爆炸 |
| 每域独立 Checkpoint 库 | 运维与本地开发成本陡增，阻碍 EP08 上线 |
| 与 EP06 记忆 MVP 并行 | 边界混乱（图内 trim vs 远程图 vs 队列） |

| MVP 后增量改 | 收益 |
|:-------------|:-----|
| 先 EP06 内嵌图 + EP08 单机 | 产品可演示、面试可讲全链路 |
| EP11 队列 → EP13 多容器 → Remote Graph | 每一步有 Harness 门禁 |
| EP14 TKE | Compose 已验证的镜像与 Helm 直接上移 |

## 史诗依赖（建议顺序）

```text
EP00–EP10（MVP）
    ↓
EP11 记忆运维（队列 / 溯源 / 监控）
EP12 记忆评测（离线回归）
    ↓
EP13 本地分布式仿真（Compose profile、注册表、Remote Graph 热插拔）
    ↓
EP14 K8s + 腾讯云 TKE（Helm、Ingress+SSE、滚动发布）
```

EP11 与 EP13 **可部分并行**：队列 Worker 先落地，再拆 Remote Graph。

## 分布式架构：企业图 vs MemoryOS 瘦身版

原「微内核 + Nacos/Etcd/MySQL + 多 Checkpoint 库」思想保留，**中小企业落地**收敛为：

| 企业全量图 | MemoryOS 瘦身版（EP13） |
|:-----------|:--------------------------|
| Nacos + Etcd + MySQL | **单配置源**：PG `graph_registry` 表（成长后再 Nacos） |
| 微内核「永不改动」 | **主编排版本化**（路由表 v1/v2，可回滚） |
| 每域独立 Checkpoint 库 | **单 PostgreSQL**（业务 + 可选 checkpoint 表前缀） |
| 长轮询配置中心 | 注册 API + **健康检查摘除** + 可选 watch |
| 多 RemoteGraph 域 | 先 **chat / rag-agent / 新子图** 三实例演示热插拔 |

**热插拔最小闭环**（EP13 验收）：

1. 子图容器启动 → 调注册 API（name、url、version、health_url）
2. 主编排按 registry 路由；health 失败自动摘除
3. 停掉某一子图容器，主编排与其它子图仍可用
4. 对外 **SSE 契约不变**（BFF / `start|token|done`）

## Remote Graph 与 LangGraph

| 阶段 | 工具 | 用途 |
|:-----|:-----|:-----|
| 开发 | `langgraph dev` | 子图热更新、Studio 调试 |
| 生产-like 本地 | `langgraph up` 或 Compose 内 `langgraph-api` | 与主编排解耦 |
| 调用 | LangGraph SDK / Agent Server HTTP | `LANGGRAPH_MODE=embedded|remote` 开关 |

首版 **不强制** LangGraph checkpoint 落库；history 仍可由 API `messages` 表注入（与 `langgraph-chat.md` 一致）。

## 学习路线

| 文档 | 对应史诗 |
|:-----|:---------|
| [L09 分布式编排](./learning/L09-distributed-orchestration.md) | EP13 + EP14 |
| [L06 部署](./learning/L06-deployment.md) | EP08（MVP 单机） |

## 技术文档（待写）

| 文档 | 史诗 |
|:-----|:-----|
| `docs/tech/distributed-orchestration.md` | EP13 |
| `docs/architecture/distributed-hotplug.md` | EP13（架构图瘦身版） |
| `docs/tech/k8s-tencent-deploy.md` | EP14 |

## 与现有史诗的轻量交叉（不扩 scope）

| 史诗 | MVP 内 | MVP 后指向 |
|:-----|:-------|:-----------|
| EP07 工作流 | P2 可裁剪 | 与 EP13 共用 `langgraph.json`，画布 UI 延后 |
| EP08 部署 | 单机 Compose + 腾讯云 | EP14 上移 TKE；**不**在 EP08 做注册中心 |
| EP09 优化 | 限流/降级 | 多副本限流在 EP13 Compose 验证 |
| EP10 面试 | 架构话术 | 分布式图作为 **加分叙事**，非 MVP 必交付 |
