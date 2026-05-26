## Context

- **现状**：`users.password_hash` 可空；`POST /users` 无密码；无 auth 路由。
- **约束**：统一响应 `{ code, message, data }`；分层 Router → Service → Repository；Redis 黑名单 key 已预留（3.4 可选不做）。
- **范围**：Story 3.4 only。

## Goals / Non-Goals

**Goals:**

- bcrypt 哈希密码；JWT access token（HS256，secret 来自 env）。
- `Authorization: Bearer <token>`；`get_current_user` 解析 `sub` 为 user id。
- Harness 覆盖 register/login/me 契约。
- 前端最小登录流：登录成功存 token，后续请求带 Header。

**Non-Goals:**

- Refresh token / Redis 黑名单（follow-up task 或 Story 3.3 可选项）。
- 改造所有 conversations 为严格 user_id 匹配（可 follow-up）。
- httpOnly Cookie（首版 localStorage + 文档说明风险）。

## Decisions

### D1: PyJWT + bcrypt

- **选择**：`PyJWT` 编解码，`bcrypt` 库直接哈希（避免 passlib 与新版本 bcrypt 兼容问题）。
- **备选**：python-jose — 功能重叠，选更常用 PyJWT。

### D2: Token payload

```json
{ "sub": "<user_uuid>", "exp": <unix> }
```

- Access TTL 默认 60 分钟（可配置）。

### D3: Auth 路由前缀

- `POST /api/v1/auth/register` body: `{ email, password }`
- `POST /api/v1/auth/login` body: `{ email, password }` → `{ access_token, token_type: "bearer" }`
- `GET /api/v1/me` → `UserRead`

### D4: 现有 POST /users

- 保留供 harness/测试，文档标 **deprecated**；或改为需 admin（本 change 保留 + 注释 deprecated）。

### D5: 前端 Token

- `localStorage` key `memoryos_access_token`；401 清 token 并跳转 `/login`（基础页）。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| localStorage XSS | EP09 可改 httpOnly；文档说明 |
| JWT secret 泄露 | 仅 env；`.env.example` 占位 |
| 明文密码进日志 | 禁止 log request body password |

## Migration Plan

1. 无强制 DB migration（password_hash 已存在）；新注册用户必填 password。
2. `pnpm setup:api` 安装新依赖。
3. 更新 `.env` JWT_SECRET。
