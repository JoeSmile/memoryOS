# EP13 — 本地分布式仿真与 Remote Agent 热插拔（MVP 后）

| 属性 | 值 |
|:-----|:---|
| **周期** | EP08 + EP11 之后（12 周计划外 backlog） |
| **优先级** | P2 |
| **依赖** | EP08（Compose 全栈）、EP11 Story 11.1（队列 Worker）、EP02/EP05 图稳定 |
| **学习路线** | [L09 分布式编排](../learning/L09-distributed-orchestration.md) |
| **路线图** | [post-mvp-roadmap.md](../post-mvp-roadmap.md) |
| **目标文档** | `docs/tech/distributed-orchestration.md` · `docs/architecture/distributed-hotplug.md` 📋 |

> 在本地 Docker 模拟 **多容器、Worker 分离、Remote Graph 注册与热插拔**；不上 K8s（见 EP14）。对外 SSE / BFF 契约 **不变**。

---

## 架构目标（瘦身版）

```text
浏览器 → Next BFF → API（主编排：鉴权 / SSE 聚合 / 动态路由）
                      ↓ registry 查表 + health
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
  langgraph-chat   langgraph-*   worker×N（EP11 队列）
        ↓             ↓
   postgres、redis（单库；checkpoint 表前缀可选）
   graph_registry（PG 表，首版配置中心）
```

**不做（本史诗）**：Nacos+Etcd 双栈、每域独立 Checkpoint 库、服务网格。

---

## Story 13.1 Compose 分布式 profile

- [ ] `infra/docker/docker-compose.yml` 增加 `profiles: [distributed]`
- [ ] 服务：`api`、`worker`（EP11）、`web`、`nginx`、`postgres`、`redis`
- [ ] 可选 `api` ×2（仅 REST 路由；chat SSE 先单实例或文档说明粘滞）
- [ ] `pnpm` / 脚本：`compose:up:distributed`
- [ ] healthcheck + `depends_on` 与 EP08 一致

**验收**：`docker compose --profile distributed up` 一键起全栈；Harness 在 compose 网络内跑绿。

---

## Story 13.2 图注册表与热插拔 API

- [ ] 表 `graph_registry`：`name`、`base_url`、`version`、`health_path`、`enabled`、`registered_at`
- [ ] `POST /internal/graphs/register`（子图启动自注册，内网 token）
- [ ] `GET /internal/graphs`（主编排拉取）；定时 health check，失败 **自动 disabled**
- [ ] 管理：手动 enable/disable（无需重启 API）
- [ ] Harness：注册 → 路由成功 → 停子图 → 路由失败可预期

**验收**：演示「新增业务子图随时上线」；停掉 chat 子图后其它已注册图仍可调。

---

## Story 13.3 Remote Graph 接入

- [ ] `langgraph.json` 导出当前 `chat_graph`（与 `apps/api/app/graphs/` 对齐）
- [ ] 本地 `langgraph dev` 文档化；Compose 内 `langgraph-chat` 服务（`langgraph up` 或等价镜像）
- [ ] API 配置：`LANGGRAPH_MODE=embedded|remote`、`LANGGRAPH_CHAT_URL`
- [ ] `ChatService` / runner：remote 时 SDK 调 Agent Server **流式**；SSE 帧形状不变
- [ ] 第二个子图容器（如 mock `agent-tools`）验证多 graph 注册
- [ ] Harness：`embedded` 与 `remote` 双模式契约（mock remote）

**验收**：切换 env 即可 embedded ↔ remote；remote 下 L02 流式 + Stop 回归仍绿。

---

## Story 13.4 主编排路由与降级

- [ ] 按 `assistant_id` / `graph_name` / 路由规则选 registry 项
- [ ] 子图超时、连接失败 → 明确 error 事件（不拖垮主编排进程）
- [ ] 可选：熔断（连续失败 N 次暂时摘除）
- [ ] LangSmith trace 标注 `graph_name`、`remote_url`

**验收**：故意错 URL 时用户看到业务错误而非 API 进程崩溃。

---

## Story 13.5 文档与面试素材

- [ ] `docs/tech/distributed-orchestration.md`：与全量企业图对比、瘦身理由
- [ ] `docs/architecture/distributed-hotplug.md`：Mermaid 图 + 热插拔演示步骤
- [ ] EP10 口述稿补充：Remote Agent、注册中心、SSE 多副本注意点

---

## 与 EP11 / EP07 边界

| 史诗 | 边界 |
|:-----|:-----|
| EP11 | Worker 队列实现；EP13 提供 **多 worker 容器** 部署形态 |
| EP07 | 可视化工作流 UI **不**挡 EP13；共用 `langgraph.json` |
| EP14 | K8s 编排；EP13 仅 Docker Compose |

---

## 同步学习

- [ ] Remote Graph vs 内嵌图（理解 / 落地）
- [ ] 注册中心瘦身：PG 表 vs Nacos（理解）
- [ ] SSE + 多 API 副本粘滞（理解）
