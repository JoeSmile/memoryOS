# infra/nginx — MemoryOS 反向代理

用于 `docker compose --profile full` 的 **nginx** 服务。云上 Ingress 应对齐相同 path 规则。

## 路由

| Path | Upstream | 说明 |
|:-----|:---------|:-----|
| `/` | `web:3000` | Next.js 页面 |
| `/api/chat` | `web:3000` | BFF（AI SDK SSE） |
| `/api/v1/chat/completions` | `api:8000` | FastAPI SSE（`proxy_buffering off`） |
| `/api/v1/*` | `api:8000` | REST API |

## SSE

`default.conf` 对 chat 相关 location 设置：

- `proxy_buffering off`
- `proxy_cache off`
- `proxy_read_timeout 3600s`

## 与 K8s Ingress（EP14）对照

| Nginx location | Ingress 等价 |
|:---------------|:-------------|
| `/api/v1/chat/completions` | 单独 path + `nginx.ingress.kubernetes.io/proxy-buffering: "off"` |
| `/api/chat` | 指向 web Service，同上 |
| `/api/v1/` | api Service |
| `/` | web Service |

## 本地验证

```bash
cd infra/docker
docker compose --env-file .env.deployment.local --profile full up -d
curl -sS http://localhost:8080/health   # 经 web 或需走 /api/v1 — 见 deployment.md
```
