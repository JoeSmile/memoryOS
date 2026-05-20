# L06 — 部署与 CI/CD（第 8 周）

**对应史诗**：EP08

---

- [ ] 📖 多阶段 Dockerfile：builder vs runtime
- [ ] 🔧 落地：镜像 < 合理体积（记录 before/after）
- [ ] 📖 Docker Compose 网络与服务发现
- [ ] 🔧 落地：`infra/docker/docker-compose.yml` 一键 up
- [ ] 📖 Nginx SSE：`proxy_buffering off`、超时、HTTP/2 注意点
- [ ] 🔧 落地：`infra/nginx/` 配置 + 本地验证流式
- [ ] 📖 腾讯云：安全组、SSH、证书
- [ ] 🔧 落地：公网 HTTPS 可访问
- [ ] 📖 GitHub Actions secrets、环境分离
- [ ] 🔧 落地：push main 自动部署（或手动 workflow_dispatch）

---

## 自测

- [ ] 新人按 README 可在 30 分钟内本地 Docker 起全栈  
- [ ] 生产环境 LangSmith / DB 密钥不在镜像内
