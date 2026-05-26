## Why

EP03 Story 3.4：会话与用户 API 目前无鉴权，`POST /users` 为开发临时接口。需要 **JWT + bcrypt** 登录体系、`GET /me` 与 Bearer 依赖，并为 EP02 前端聊天与 SSE 提供 Token 传递基础。

Story 3.5 另开 change `ep03-db-optimize`（本 change 不包含索引/事务优化）。

## What Changes

- 新增 `POST /api/v1/auth/register`、`POST /api/v1/auth/login`（返回 access token）。
- 新增 `GET /api/v1/me`（Bearer 鉴权）。
- 新增 `get_current_user` 依赖；`conversations` 等路由逐步改为鉴权用户（本 change 至少保护 `/me`，conversations 可选绑定 user_id 校验）。
- 配置：`JWT_SECRET`、`ACCESS_TOKEN_EXPIRE_MINUTES` 等；`.env.example` 更新。
- 依赖：`python-jose`/`PyJWT`、`passlib[bcrypt]`。
- 前端：`apps/web` 登录页 + API client Token 拦截器（localStorage，design 说明 trade-off）。
- Harness L1：`test_auth_contract.py`。
- **不引入**：Refresh token 黑名单（可选子 task）、OAuth、EP02 SSE 鉴权（EP02 change）。

## Capabilities

### New Capabilities

- `jwt-auth`: 注册、登录、JWT 签发与校验、`GET /me`。

### Modified Capabilities

- `data-access-layer`: 受保护路由使用 `Depends(get_current_user)`；`UserService` 支持密码哈希。

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `apps/api/app/core/` | `security.py` 或 `deps.py`、config |
| `apps/api/app/api/v1/auth.py` | 新路由 |
| `apps/api/app/services/` | `auth_service.py` |
| `apps/web/` | 登录页、`lib/api-client` |
| `tests/harness/` | auth 契约 |
| 依赖 | PyJWT/passlib |
