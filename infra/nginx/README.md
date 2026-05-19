# infra/nginx

Nginx 反向代理配置，用于生产环境统一入口。

## 规划内容（EP08）

- SSE 流式转发：`proxy_buffering off`、`proxy_read_timeout`
- HTTPS 与 HTTP → HTTPS 重定向
- 前端静态资源与 `_next/static` 缓存
- API upstream 负载到 `apps/api`

## 占位说明

当前目录为 Story 1.1 占位；具体配置在 **Story 8.3** 编写。
