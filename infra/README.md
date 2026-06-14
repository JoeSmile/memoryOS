# infra — 运维与部署配置

容器化、反向代理、编排等与运行环境相关的配置，**不包含**业务代码。

| 目录 | 说明 |
|:-----|:-----|
| [`docker/`](./docker/) | **EP03** 本地 PostgreSQL Compose；EP08 全栈编排 |
| [`nginx/`](./nginx/) | Nginx 反向代理：SSE、HTTPS、静态资源（Story 8.3） |

## 预期产物（后续迭代）

```
infra/
├── docker/
│   ├── docker-compose.yml      # 本地：pg+redis（EP03）→ 全栈（EP08）→ profile distributed（EP13）
│   └── ...
├── k8s/ 或 deploy/helm/        # EP14
└── nginx/
```

MVP 后演进：[docs/tasks/post-mvp-roadmap.md](../docs/tasks/post-mvp-roadmap.md)

## 本地数据库（EP03 已可用）

```bash
pnpm db:up    # 仓库根目录；或 cd infra/docker && docker compose up -d
```

见 [docker/README.md](./docker/README.md)。表设计见 [docs/database.md](../docs/database.md)。

## 全栈一键启动（Story 8.2 完成后）

```bash
cd infra/docker && docker compose up -d   # web + api + nginx + pg + redis
```

分布式 profile（EP13，MVP 后）：

```bash
docker compose --profile distributed up -d
```
