# L06 — 部署与 CI/CD（第 8 周）

**对应史诗**：EP08

---

## 1. Docker 多阶段构建

### 学什么

- [ ] 📖 阶段：deps install → build → runtime（alpine/slim）
- [ ] 📖 Next `output: "standalone"` 拷贝 static/public
- [ ] 📖 非 root 用户、`.dockerignore`、层缓存（先 COPY package.json）
- [ ] 🔧 `apps/web/Dockerfile`、`apps/api/Dockerfile`

### 面试常问

- 如何缩小 Node 镜像？standalone 解决什么问题？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 未拷 `.next/static` | 页面无样式 | Dockerfile 三步拷贝 |
| 构建上下文过大 | 慢 | dockerignore node_modules |
| arm vs amd 镜像 | 云上跑不起来 | buildx 指定平台 |

---

## 2. Docker Compose 全栈

### 学什么

- [ ] 📖 服务：web、api、postgres、redis、nginx
- [ ] 📖 网络：服务名 DNS、`depends_on` + healthcheck
- [ ] 📖 卷：pg 数据持久化
- [ ] 🔧 `infra/docker/docker-compose.yml` 一键 `up`

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| api 用 localhost 连 db | 容器内连不上 | host=postgres |
| 无 healthcheck 就启动 web | 502 | 等 pg ready |
| .env 提交进镜像 | 密钥泄露 | runtime env 注入 |

---

## 3. Nginx 反向代理

### 学什么

- [ ] 📖 `proxy_pass` upstream；`client_max_body_size` 上传
- [ ] 📖 SSE：`proxy_buffering off`、`proxy_cache off`、读超时 ↑
- [ ] 📖 HTTPS：certbot / 腾讯云证书、HTTP→HTTPS
- [ ] 🔧 `infra/nginx/memoryos.conf`

### 面试常问

- 为什么 SSE 在 Nginx 后容易「不流式」？怎么配？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 默认 buffering | 一次性吐完 | off buffering |
| HTTP/2 某些组合问题 | 连接断 | 查官方建议，必要时 HTTP/1.1 到 upstream |
| CORS 双头 | 浏览器拦 | 只在一处设 CORS |

---

## 4. 腾讯云与运维

### 学什么

- [ ] 📖 安全组：80/443/22；SSH 密钥
- [ ] 📖 环境变量：dev/staging/prod 分离
- [ ] 📖 数据库：托管 PG 或容器；备份策略
- [ ] 🔧 域名 + HTTPS 可访问

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 轻量机内存 2G 跑全栈 | OOM | 限制容器 memory |
| 时区 UTC 乱 | 日志对不上 | TZ=UTC |

---

## 5. GitHub Actions CI/CD

### 学什么

- [ ] 📖 流水线：lint → test → build image → deploy
- [ ] 📖 Secrets：SSH key、API keys；不写进日志
- [ ] 📖 缓存：pnpm store、Docker layer；**15.5** 生产默认 Webpack 缓存 vs `next build --turbopack` Beta（升级 16 后再统一 Turbopack CI 缓存）
- [ ] 🔧 `.github/workflows/deploy.yml`

### 面试常问

- 如何实现零停机或回滚？蓝绿 vs 滚动？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| main 直接部署无门禁 | 线上炸 | 加 lint/test 必过 |
| 镜像 tag 只用 latest | 难回滚 | git sha tag |
| migration 在旧代码上新 schema | 不兼容 | 先扩表后发版 |

---

## 阶段自测

- [ ] 新人 30 分钟 Compose 起全栈  
- [ ] curl SSE 经 Nginx 仍流式  
- [ ] 说清 standalone 目录结构与启动命令

---

## MVP 后（不占 EP08 范围）

- [ ] 📖 分布式 Compose profile、Remote Graph、注册热插拔 → [L09](./L09-distributed-orchestration.md)
- [ ] 📖 EP08 单机与 EP14 TKE 如何选型 → [post-mvp-roadmap.md](../post-mvp-roadmap.md)
