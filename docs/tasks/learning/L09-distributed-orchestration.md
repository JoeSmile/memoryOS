# L09 — 分布式编排与 Remote Agent（MVP 后）

**对应史诗**：EP13 + EP14（不占 12 周主排期）  
**前置**：完成 [L06 部署](./L06-deployment.md)（EP08）、[L05 记忆](./L05-memory-workflow.md)（EP06）、[L02 LangGraph](./L02-streaming-langgraph.md)

> 学习顺序：**先队列多容器（EP11+EP13）→ Remote Graph → 注册热插拔 → K8s**。  
> 路线图：[post-mvp-roadmap.md](../post-mvp-roadmap.md)

---

## 1. 为什么 MVP 后再做分布式？

### 学什么

- [ ] 📖 内嵌 LangGraph vs Remote Agent Server 边界
- [ ] 📖 「微内核 + 注册中心」解决什么问题（独立发版、故障隔离）
- [ ] 📖 中小企业瘦身：单 PG 注册表、单库、避免 Nacos+Etcd 双栈
- [ ] 📖 MemoryOS 策略：**EP02–EP10 不改成注册中心架构**

### 面试常问

- 为什么不在第一个版本就上 K8s 和微服务？
- Remote Graph 和「把 FastAPI 拆多个服务」有什么区别？

---

## 2. Docker Compose 分布式 profile（EP13）

### 学什么

- [ ] 📖 `profiles`、`scale worker`、容器 DNS
- [ ] 📖 API 与 Worker 分离（衔接 EP11 队列）
- [ ] 📖 SSE 多 API 副本：粘滞会话 vs chat 单副本
- [ ] 🔧 `infra/docker/docker-compose.yml` `--profile distributed`

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| worker 连 localhost redis | 队列不消费 | host=redis |
| 双 api 跑 SSE 无粘滞 | 流式随机断 | chat 单副本或 Ingress affinity |
| 子图未注册 | 404 / 空路由 | 启动脚本调 register API |

---

## 3. Remote Graph 与 LangGraph CLI（EP13）

### 学什么

- [ ] 📖 `langgraph dev` vs `langgraph up`（内存 vs Docker+PG）
- [ ] 📖 Agent Server API 与现有 SSE 聚合层关系
- [ ] 📖 `langgraph.json` 与 `apps/api/app/graphs/` 对齐
- [ ] 🔧 `LANGGRAPH_MODE=remote` 本地联调

### 面试常问

- 图放 API 进程里和放独立 Agent Server 各有什么优缺点？
- checkpoint 和 DB messages 表双写有什么问题？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| remote 后 SSE 帧变了 | 前端解析失败 | Harness 契约锁形状 |
| Safari + localhost Studio | 连不上 | `--tunnel` 或 Chrome |

---

## 4. 注册表与热插拔（EP13）

### 学什么

- [ ] 📖 注册 API：name、url、version、health
- [ ] 📖 健康检查摘除 vs 长轮询配置中心
- [ ] 📖 主编排降级：子图失败不拖垮进程
- [ ] 🔧 `graph_registry` 表 + internal API

### 面试常问

- 如何实现 Agent 热插拔而不重启主编排？
- Nacos 和数据库注册表怎么选？

---

## 5. 本地 K8s（EP14）

### 学什么

- [ ] 📖 k3d / kind 与 Docker Compose 差异
- [ ] 📖 Helm chart、values 多环境
- [ ] 📖 Readiness 与注册中心联动
- [ ] 🔧 `helm install` 本地 smoke

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| Ingress 缓冲 SSE | 不流式 | buffering off、超时 |
| 镜像 arm/amd 不一致 | CrashLoop | buildx 平台 |

---

## 6. 腾讯云 TKE（EP14）

### 学什么

- [ ] 📖 TKE + TCR + CLB 与 EP08 轻量 Docker 对比
- [ ] 📖 云 PostgreSQL / Redis 迁移注意点
- [ ] 📖 从 Compose 到 Helm 的迁移路径（同镜像）

### 阶段自测

- [ ] 能画 **瘦身版** 热插拔架构图（对比企业全量图差什么）
- [ ] 能演示：起子图 → 注册 → 停子图 → 主编排仍可用
- [ ] 能说明 EP08 单机与 EP14 TKE 如何选型

---

## 官方参考

| 主题 | 链接 |
|:-----|:-----|
| LangGraph CLI | https://docs.langchain.com/langsmith/cli |
| Local dev vs `langgraph up` | https://docs.langchain.com/langsmith/local-dev-testing |
| k3d | https://k3d.io |
