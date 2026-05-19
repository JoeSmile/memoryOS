# infra — 运维与部署配置

容器化、反向代理、编排等与运行环境相关的配置，**不包含**业务代码。

| 目录 | 说明 |
|:-----|:-----|
| [`docker/`](./docker/) | Dockerfile、docker-compose 片段（Story 8.1–8.2） |
| [`nginx/`](./nginx/) | Nginx 反向代理：SSE、HTTPS、静态资源（Story 8.3） |

## 预期产物（后续迭代）

```
infra/
├── docker/
│   ├── docker-compose.yml      # 本地全栈：web + api + postgres + redis
│   └── ...
└── nginx/
    ├── nginx.conf
    └── conf.d/memoryos.conf
```

## 本地一键启动（Story 8.2 完成后）

```bash
docker compose -f infra/docker/docker-compose.yml up -d
```
