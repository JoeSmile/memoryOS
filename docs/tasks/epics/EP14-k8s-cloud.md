# EP14 — K8s 编排与腾讯云生产（MVP 后）

| 属性 | 值 |
|:-----|:---|
| **周期** | EP13 本地 Compose 跑通后 |
| **优先级** | P2 |
| **依赖** | EP08（镜像与 CI）、EP13（分布式架构与 Helm 输入） |
| **学习路线** | [L09 §4–5](../learning/L09-distributed-orchestration.md) |
| **路线图** | [post-mvp-roadmap.md](../post-mvp-roadmap.md) |
| **目标文档** | `docs/tech/k8s-tencent-deploy.md` 📋 |

> 将 EP13 验证过的 **多服务 + Remote Graph + Worker** 上到 **本地 k3d/kind**，再迁 **腾讯云 TKE**。EP08 轻量单机仍保留为成本最低路径。

---

## Story 14.1 本地 K8s（k3d 或 kind）

- [ ] `infra/k8s/` 或 `deploy/helm/memoryos/` chart 骨架
- [ ] Values：`local`（资源收紧）、`staging`
- [ ] Deployment：api、web、worker、langgraph-chat（+ 可选第二子图）
- [ ] Service、ConfigMap、Secret（对齐 `.env.production.example`）
- [ ] 文档：一键 `k3d cluster create` + `helm install`

**验收**：本机 k3d 内 curl Ingress 可打开 web；chat SSE 流式成功。

---

## Story 14.2 Ingress 与 SSE

- [ ] Ingress-Nginx（或 TKE Ingress）：`proxy-buffering` off、读超时 ↑
- [ ] chat 流式 Deployment：**1 副本** 或 **session affinity**（与 EP13 文档一致）
- [ ] REST / worker 可独立 scale
- [ ] TLS：本地 mkcert 或 staging 证书

**验收**：经 Ingress 长连接流式不断；多 api 副本策略有书面说明。

---

## Story 14.3 健康检查与滚动发布

- [ ] Liveness / Readiness：api、worker、langgraph 子图
- [ ] Readiness 失败 → 从 registry 摘除（衔接 EP13）或 K8s 仅路由健康 Pod
- [ ] `helm upgrade` 滚动发布；Harness smoke 在 staging
- [ ] 回滚：`helm rollback` 或 `MEMORY_ENABLED` / `LANGGRAPH_MODE` 开关

**验收**：发布过程中无大面积 502；旧 Pod  draining 时 SSE 行为可接受。

---

## Story 14.4 腾讯云 TKE

- [ ] TCR 镜像仓库；CI 推镜像（延续 EP08 Actions）
- [ ] TKE 集群（先单节点池）；CLB + Ingress
- [ ] 数据库：TDSQL-C / 云 PostgreSQL；云 Redis（或初期仍轻量自建）
- [ ] 安全组、密钥（与 EP08 Secrets 策略一致）
- [ ] 可选：注册中心仍用 PG 表；成长后再迁 Nacos 托管

**验收**：与 EP08 同域名或 staging 域名可访问；核心 Harness smoke 对 staging 绿。

---

## Story 14.5 可观测与成本

- [ ] 云监控 / 日志采集钩子
- [ ] EP11 记忆 metrics 在 K8s 环境可采集
- [ ] LangSmith 生产采样（衔接 EP09 Story 9.7）
- [ ] 单节点池成本说明 vs 轻量 Docker（EP08）

---

## 与 EP08 关系

| EP08（MVP） | EP14（成长） |
|:------------|:-------------|
| 轻量服务器 + Docker Compose | TKE + Helm |
| 单机 nginx + SSE | Ingress + 多副本策略 |
| GitHub Actions deploy | 推 TCR + helm upgrade |

**不替换 EP08**：小企业/演示仍可用单机路径。

---

## 同步学习

- [ ] Helm values 与环境分离（理解 / 落地）
- [ ] TKE 与轻量 Docker 选型（理解）
- [ ] K8s 下 SSE 与 HPA 限制（理解）
