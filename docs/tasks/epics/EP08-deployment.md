# EP08 — 工程化与腾讯云部署

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 8 周 |
| **优先级** | P0 |
| **学习路线** | [L06-deployment.md](../learning/L06-deployment.md) |

---

## Story 8.1 Docker

- [ ] `apps/web`、`apps/api` 多阶段 Dockerfile
- [ ] `.dockerignore`、非 root 用户

## Story 8.2 Docker Compose

- [ ] 本地一键：web、api、postgres、redis、nginx
- [ ] `.env.production.example`

## Story 8.3 Nginx

- [ ] SSE：`proxy_buffering off`、超时
- [ ] HTTPS、静态资源、CORS

## Story 8.4 腾讯云

- [ ] 轻量服务器、Docker、安全组

## Story 8.5 线上数据

- [ ] 生产 PG + Redis、Alembic 迁移
- [ ] dev / staging / prod 环境隔离

## Story 8.6 域名与 SSL

- [ ] 解析、证书、全站 HTTPS

## Story 8.7 CI/CD

- [ ] GitHub Actions：lint → build → deploy
- [ ] Secrets 管理

---

## 同步学习

- [ ] Docker 多阶段与网络（理解 / 落地）
- [ ] Nginx SSE 避坑（理解 / 落地）
- [ ] 云服务器运维（理解 / 落地）
- [ ] CI/CD 与密钥安全（理解 / 落地）
